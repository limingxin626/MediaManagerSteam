package com.example.myapplication.ui.viewmodel

import android.content.Context
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.Pager
import androidx.paging.PagingConfig
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.Message
import com.example.myapplication.data.database.entities.MessageWithDetails
import com.example.myapplication.data.model.ProgressRequestBody
import com.example.myapplication.data.repository.MessageRepository
import com.example.myapplication.data.service.ClientMediaFile
import com.example.myapplication.data.service.MessageSyncRequest
import com.example.myapplication.data.service.SyncNetwork
import com.example.myapplication.utils.MediaFileInfo
import com.example.myapplication.utils.MediaFilePicker
import com.example.myapplication.utils.ThumbnailGenerator
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MultipartBody
import java.io.File
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

/**
 * 消息视图模型
 */
class MessageViewModel(private val messageRepository: MessageRepository) : ViewModel() {
    // 搜索查询
    private val _searchQuery = MutableStateFlow("")
    val searchQuery = _searchQuery.asStateFlow()

    // 发送中状态（文件预处理 + DB 事务完成前为 true）
    private val _isSending = MutableStateFlow(false)
    val isSending = _isSending.asStateFlow()

    // 标签过滤
    private val _tagId = MutableStateFlow<Long?>(null)

    // 演员过滤
    private val _actorId = MutableStateFlow<Long?>(null)

    // 分页消息列表
    @OptIn(ExperimentalCoroutinesApi::class)
    val messagesPaged: Flow<PagingData<MessageWithDetails>> = combine(_searchQuery, _tagId, _actorId) { query, tagId, actorId ->
        Triple(query, tagId, actorId)
    }.flatMapLatest { (query, tagId, actorId) ->
        Pager(
            config = PagingConfig(pageSize = 30, prefetchDistance = 10),
            pagingSourceFactory = {
                when {
                    actorId != null -> messageRepository.getMessagesByActorPaged(actorId, query)
                    tagId != null   -> messageRepository.getMessagesByTagPaged(tagId, query)
                    else            -> messageRepository.getMessagesPaged(query)
                }
            }
        ).flow
    }.cachedIn(viewModelScope)

    // UI状态
    private val _uiState = MutableStateFlow(UIState())
    val uiState: StateFlow<UIState> = _uiState.asStateFlow()

    fun searchMessages(query: String) { _searchQuery.value = query }
    fun clearSearch() { _searchQuery.value = "" }
    fun setTagId(tagId: Long?) { _tagId.value = tagId }
    fun setActorId(actorId: Long?) { _actorId.value = actorId }

    fun refreshMessages() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }

    fun clearError() { _uiState.value = _uiState.value.copy(error = null) }
    fun clearMessage() { _uiState.value = _uiState.value.copy(message = null) }

    fun toggleStarred(messageId: Long) {
        viewModelScope.launch {
            try {
                messageRepository.toggleStarred(messageId)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = "操作失败: ${e.message}")
            }
        }
    }

    fun deleteMessage(messageId: Long) {
        viewModelScope.launch {
            try {
                messageRepository.deleteMessage(messageId)
                _uiState.value = _uiState.value.copy(message = "消息删除成功")
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = "删除失败: ${e.message}")
            }
        }
    }

    /**
     * 发送消息（文本 + 媒体附件）
     * Android 直接创建完整 Message 记录（sendStatus=PUSHING），立刻进入 paging。
     * 后台上传文件并推送给后端，后端接受客户端 ID。
     */
    fun sendMessage(
        text: String,
        mediaList: List<MediaFileInfo>,
        databaseManager: DatabaseManager,
        context: Context,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        viewModelScope.launch {
            _isSending.value = true
            val filePicker = MediaFilePicker(context)
            val thumbnailGenerator = ThumbnailGenerator(context)

            // Step 1: 在主线程外预处理所有媒体文件（复制、哈希、缩略图）
            data class PreparedMedia(val info: MediaFileInfo, val localPath: String?, val entity: Media)

            val preparedList = withContext(Dispatchers.IO) {
                mediaList.mapIndexed { _, mediaFileInfo ->
                    val localPath = filePicker.copyFileToAppStorage(mediaFileInfo.uri, mediaFileInfo.fileName)
                    val fileHash = filePicker.computeBlake2bHash(mediaFileInfo.uri) ?: mediaFileInfo.uri.toString()
                    val resolution = filePicker.getMediaResolution(mediaFileInfo.uri)
                    val isVideo = mediaFileInfo.mimeType?.startsWith("video/") == true
                    val durationMs = if (isVideo) filePicker.getVideoDuration(mediaFileInfo.uri)?.let { it * 1000 } else null
                    val thumbnailPath = localPath?.let { thumbnailGenerator.generateThumbnail(it, isVideo) }
                    PreparedMedia(
                        info = mediaFileInfo,
                        localPath = localPath,
                        entity = Media(
                            fileHash = fileHash,
                            localMediaPath = localPath,
                            localThumbnailPath = thumbnailPath,
                            mimeType = mediaFileInfo.mimeType,
                            fileSize = mediaFileInfo.size,
                            width = resolution?.split("x")?.getOrNull(0)?.toIntOrNull(),
                            height = resolution?.split("x")?.getOrNull(1)?.toIntOrNull(),
                            durationMs = durationMs
                        )
                    )
                }
            }

            // Step 2: 判断是否在线，决定初始状态
            val isOnline = !databaseManager.syncPreferences.isOfflineMode.value &&
                           databaseManager.networkMonitor.isWifiConnected.value == true
            val initialStatus = if (isOnline) Message.MSG_STATUS_PUSHING else Message.MSG_STATUS_PENDING_SYNC

            // 单事务写入 Message + 所有 Media + junctions + tags → PagingData 只刷新一次
            val (localMessageId, mediaIds) = messageRepository.createMessageWithMedia(
                message = Message(text = text.ifBlank { null }, sendStatus = initialStatus),
                mediaEntities = preparedList.map { it.entity },
                tagRepository = databaseManager.tagRepository
            )
            // ↑ 至此消息已在 paging 中完整可见（带全部本地缩略图）
            _isSending.value = false

            // Step 3: 后台上传 + 推送（离线时跳过，由 WorkManager/retrySync 重试）
            if (!isOnline) {
                Log.d(TAG, "sendMessage 跳过上传：离线模式或无 WiFi 连接，消息已本地保存")
                return@launch
            }
            try {
                val uploadResults = coroutineScope {
                    preparedList.mapIndexed { index, prepared ->
                        async {
                            val serverPath = uploadFile(prepared.info, prepared.localPath)
                            if (serverPath != null) ClientMediaFile(id = mediaIds[index], file_path = serverPath) else null
                        }
                    }.awaitAll()
                }
                if (uploadResults.any { it == null } && preparedList.isNotEmpty()) {
                    Log.w(TAG, "sendMessage 部分文件上传失败，标记为待同步")
                    messageRepository.updateSendStatus(localMessageId, Message.MSG_STATUS_PENDING_SYNC)
                    return@launch
                }

                val msg = messageRepository.getMessageById(localMessageId)
                val createdAtIso = msg?.let {
                    Instant.ofEpochMilli(it.createdAt)
                        .atOffset(ZoneOffset.UTC)
                        .format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                }

                val response = SyncNetwork.messageSyncService.createFromClient(
                    MessageSyncRequest(
                        id = localMessageId,
                        text = text.ifBlank { null },
                        actor_id = null,
                        created_at = createdAtIso,
                        files = uploadResults.filterNotNull()
                    )
                )

                messageRepository.applyRemoteUrls(localMessageId, response)
                onSuccess()
            } catch (e: Exception) {
                Log.e(TAG, "sendMessage 同步失败，已入队等待重试: ${e.message}", e)
                // 不标记 PUSH_FAILED（避免用户看到错误），标记 PENDING_SYNC 静默等待重试
                messageRepository.updateSendStatus(localMessageId, Message.MSG_STATUS_PENDING_SYNC)
            }
        }
    }

    /**
     * 重试推送失败的消息（重新上传所有本地媒体并调用 create-from-client）
     */
    fun retrySync(messageId: Long) {
        viewModelScope.launch {
            messageRepository.updateSendStatus(messageId, Message.MSG_STATUS_PUSHING)
            try {
                val mediaList = messageRepository.getMediaByMessageId(messageId)
                val uploadResults = coroutineScope {
                    mediaList.map { media ->
                        async {
                            val serverPath = uploadFileFromMedia(media)
                            if (serverPath != null) ClientMediaFile(id = media.id, file_path = serverPath) else null
                        }
                    }.awaitAll()
                }

                val msg = messageRepository.getMessageById(messageId)
                val createdAtIso = msg?.let {
                    Instant.ofEpochMilli(it.createdAt)
                        .atOffset(ZoneOffset.UTC)
                        .format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                }

                // 幂等：后端发现 ID 已存在则返回现有记录
                val response = SyncNetwork.messageSyncService.createFromClient(
                    MessageSyncRequest(
                        id = messageId,
                        text = msg?.text,
                        actor_id = msg?.actorId,
                        created_at = createdAtIso,
                        files = uploadResults.filterNotNull()
                    )
                )
                messageRepository.applyRemoteUrls(messageId, response)
            } catch (e: Exception) {
                Log.e(TAG, "retrySync 失败: ${e.message}", e)
                messageRepository.updateSendStatus(messageId, Message.MSG_STATUS_PUSH_FAILED)
            }
        }
    }

    /** 上传单个媒体文件，返回服务器路径 */
    private suspend fun uploadFile(mediaFileInfo: MediaFileInfo, localPath: String?): String? {
        if (localPath == null) return null
        val file = File(localPath)
        if (!file.exists()) return null
        return try {
            val body = ProgressRequestBody(file, mediaFileInfo.mimeType ?: "application/octet-stream") { }
            val part = MultipartBody.Part.createFormData("file", mediaFileInfo.fileName, body)
            SyncNetwork.uploadService.uploadMedia(part).path
        } catch (e: Exception) {
            Log.e(TAG, "uploadFile 失败 [${mediaFileInfo.fileName}]: ${e.message}", e)
            null
        }
    }

    /** 从已有 Media 实体上传文件 */
    private suspend fun uploadFileFromMedia(media: Media): String? {
        val path = media.localMediaPath ?: return null
        val file = File(path)
        if (!file.exists()) return null
        return try {
            val mimeType = media.mimeType ?: "application/octet-stream"
            val body = ProgressRequestBody(file, mimeType) { }
            val part = MultipartBody.Part.createFormData("file", file.name, body)
            SyncNetwork.uploadService.uploadMedia(part).path
        } catch (e: Exception) {
            Log.e(TAG, "uploadFileFromMedia 失败: ${e.message}", e)
            null
        }
    }

    companion object {
        private const val TAG = "MessageViewModel"
    }
}

data class UIState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null
)
