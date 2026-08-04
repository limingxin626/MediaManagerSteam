package com.example.myapplication.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.model.PushSyncResult
import com.example.myapplication.data.model.SyncResult
import com.example.myapplication.data.service.SyncPreferences
import com.example.myapplication.data.service.ThumbnailDisplayMode
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class SettingsViewModel(
    private val databaseManager: DatabaseManager
) : ViewModel() {

    private val syncPreferences: SyncPreferences = databaseManager.syncPreferences

    private val _syncState = MutableStateFlow<SyncUiState>(SyncUiState.Idle)
    val syncState: StateFlow<SyncUiState> = _syncState

    /** 是否已做过全量初始化（存在增量游标）。UI 据此提示是否需要先初始化。 */
    private val _hasCursor = MutableStateFlow(syncPreferences.getSyncCursor() != null)
    val hasCursor: StateFlow<Boolean> = _hasCursor

    /** 缩略图显示模式(马赛克 / 等分网格)。 */
    val thumbnailMode: StateFlow<ThumbnailDisplayMode> = syncPreferences.thumbnailMode

    fun setThumbnailMode(mode: ThumbnailDisplayMode) {
        syncPreferences.setThumbnailMode(mode)
    }

    /**
     * 增量同步：先推 outbox，再从上次游标拉取变更日志。
     * - 无游标 → 提示先执行「初始化」。
     * - 410（游标过期）→ 清游标并提示重新「初始化」。
     */
    fun syncIncremental() {
        if (_syncState.value is SyncUiState.Syncing) return

        val cursor = syncPreferences.getSyncCursor()
        if (cursor == null) {
            _syncState.value = SyncUiState.Error("尚未初始化，请先执行「初始化全量同步」")
            return
        }

        viewModelScope.launch {
            _syncState.value = SyncUiState.Syncing
            val results = mutableListOf<String>()

            if (!pushOutbox(results)) return@launch

            when (val r = databaseManager.messageRepository.syncIncremental(cursor.first, cursor.second)) {
                is SyncResult.Success -> {
                    r.serverTime?.let {
                        syncPreferences.setSyncCursor(it, r.serverCursorId ?: 0L)
                    }
                    results.add("增量: +${r.insertedCount} ~${r.updatedCount} -${r.deletedCount}")
                    _syncState.value = SyncUiState.Success(results.joinToString("\n"))
                }

                is SyncResult.NeedFullSync -> {
                    syncPreferences.clearSyncCursor()
                    _hasCursor.value = false
                    _syncState.value = SyncUiState.Error("游标已过期，请重新执行「初始化全量同步」")
                }

                is SyncResult.Error -> {
                    _syncState.value =
                        SyncUiState.Error("增量同步失败: ${r.message}\n${results.joinToString("\n")}")
                }
            }
        }
    }

    /**
     * 初始化全量同步：先推 outbox，再全量拉取 Collection + Message（含 Media/Tag），
     * 最后 seed 增量游标（从本次同步开始的时刻起，后续走增量）。
     */
    fun syncFull() {
        if (_syncState.value is SyncUiState.Syncing) return

        viewModelScope.launch {
            _syncState.value = SyncUiState.Syncing
            val results = mutableListOf<String>()

            if (!pushOutbox(results)) return@launch

            // 在拉取前记录游标起点，确保同步窗口内后端的新变更下次增量能覆盖
            val cursorSeed = databaseManager.messageRepository.currentServerCursorSeed()

            // 同步 Collection（必须先成功，Message 依赖 Collection 外键）
            when (val r =
                databaseManager.collectionRepository.syncFromRemote(databaseManager.appContext)) {
                is SyncResult.Success -> results.add("合集: +${r.insertedCount} ~${r.updatedCount}")
                is SyncResult.Error -> {
                    _syncState.value = SyncUiState.Error("合集同步失败: ${r.message}")
                    return@launch
                }

                else -> {}
            }

            // 同步 Message (含 Media/Tag)
            when (val r = databaseManager.messageRepository.syncFromRemote()) {
                is SyncResult.Success -> results.add("消息: +${r.insertedCount} ~${r.updatedCount}")
                is SyncResult.Error -> {
                    _syncState.value =
                        SyncUiState.Error("消息同步失败: ${r.message}\n${results.joinToString("\n")}")
                    return@launch
                }

                else -> {}
            }

            // seed 游标：优先用后端权威 server_time，做一次从 seed 起点的增量补齐
            when (val r = databaseManager.messageRepository.syncIncremental(cursorSeed)) {
                is SyncResult.Success -> {
                    syncPreferences.setSyncCursor(r.serverTime ?: cursorSeed, r.serverCursorId ?: 0L)
                }
                // 补齐失败不影响全量结果，退而用本地 seed 作为游标起点
                else -> syncPreferences.setSyncCursor(cursorSeed, 0L)
            }
            _hasCursor.value = true

            _syncState.value = SyncUiState.Success(results.joinToString("\n"))
        }
    }

    /**
     * 推送 outbox 待同步项。成功（含无待推送）返回 true；失败时置错误状态并返回 false。
     */
    private suspend fun pushOutbox(results: MutableList<String>): Boolean {
        return when (val r = databaseManager.syncOutboxRepository.syncToServer()) {
            is PushSyncResult.Success -> {
                if (r.pushedCount > 0) results.add("上传: ${r.pushedCount} 条")
                true
            }
            is PushSyncResult.Error -> {
                _syncState.value = SyncUiState.Error("上传失败: ${r.message}")
                false
            }
            is PushSyncResult.Skipped -> true
        }
    }

    fun resetState() {
        _syncState.value = SyncUiState.Idle
    }
}

sealed class SyncUiState {
    data object Idle : SyncUiState()
    data object Syncing : SyncUiState()
    data class Success(val summary: String) : SyncUiState()
    data class Error(val message: String) : SyncUiState()
}
