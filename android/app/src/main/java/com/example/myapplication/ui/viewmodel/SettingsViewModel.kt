package com.example.myapplication.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.model.SyncResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class SettingsViewModel(
    private val databaseManager: DatabaseManager
) : ViewModel() {

    private val _syncState = MutableStateFlow<SyncUiState>(SyncUiState.Idle)
    val syncState: StateFlow<SyncUiState> = _syncState

    fun syncAll() {
        if (_syncState.value is SyncUiState.Syncing) return
        viewModelScope.launch {
            _syncState.value = SyncUiState.Syncing

            val results = mutableListOf<String>()

            // 同步 Actor（必须先成功，Message 依赖 Actor 外键）
            when (val r = databaseManager.actorRepository.syncFromRemote(databaseManager.appContext)) {
                is SyncResult.Success -> results.add("演员: +${r.insertedCount} ~${r.updatedCount}")
                is SyncResult.Error -> {
                    _syncState.value = SyncUiState.Error("演员同步失败: ${r.message}")
                    return@launch
                }
                else -> {}
            }

            // 同步 Message (含 Media/Tag)
            when (val r = databaseManager.messageRepository.syncFromRemote()) {
                is SyncResult.Success -> results.add("消息: +${r.insertedCount} ~${r.updatedCount}")
                is SyncResult.Error -> {
                    _syncState.value = SyncUiState.Error("消息同步失败: ${r.message}\n${results.joinToString("\n")}")
                    return@launch
                }
                else -> {}
            }

            _syncState.value = SyncUiState.Success(results.joinToString("\n"))
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
