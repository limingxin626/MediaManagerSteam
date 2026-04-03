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
import com.example.myapplication.data.model.MediaUploadState
import com.example.myapplication.data.model.ProgressRequestBody
import com.example.myapplication.data.model.SendStatus
import com.example.myapplication.data.model.SendingMessage
import com.example.myapplication.data.repository.MessageRepository
import com.example.myapplication.data.service.CreateMessageRequest
import com.example.myapplication.data.service.SyncNetwork
import com.example.myapplication.utils.MediaFileInfo
import com.example.myapplication.utils.MediaFilePicker
import com.example.myapplication.utils.ThumbnailGenerator
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
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import okhttp3.MultipartBody
import java.io.File
import java.util.UUID

/**
 * 消息视图模型
 */
class MessageViewModel(private val messageRepository: MessageRepository) : ViewModel() {
    // 搜索查询
    private val _searchQuery = MutableStateFlow("")
    val searchQuery = _searchQuery.asStateFlow()

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

    // 发送中的消息（乐观更新列表）
    private val _sendingMessages = MutableStateFlow<Map<String, SendingMessage>>(emptyMap())
    val sendingMessages: StateFlow<Map<String, SendingMessage>> = _sendingMessages.asStateFlow()

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
     * 完全绕过 Outbox：直接 HTTP 上传 + 创建消息，本地乐观写入供即时反馈。
     */
    fun sendMessage(
        text: String,
        mediaList: List<MediaFileInfo>,
        databaseManager: DatabaseManager,
        context: Context,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        val tempId = UUID.randomUUID().toString()
        viewModelScope.launch {
            val filePicker = MediaFilePicker(context)
            val thumbnailGenerator = ThumbnailGenerator(context)

            // Step 1: 乐观写入 Room（sendStatus=PENDING）
            val localMessageId = messageRepository.createMessage(
                Message(text = text.ifBlank { null }, sendStatus = Message.MSG_STATUS_PENDING),
                immediateSync = false
            )
            parseAndAttachTags(text, localMessageId, databaseManager)

            // 写入每个媒体到本地 Room
            val initialStates = mutableListOf<MediaUploadState>()
            for ((index, mediaFileInfo) in mediaList.withIndex()) {
                val localPath = filePicker.copyFileToAppStorage(mediaFileInfo.uri, mediaFileInfo.fileName)
                val fileHash = filePicker.computeBlake2bHash(mediaFileInfo.uri) ?: mediaFileInfo.uri.toString()
                val resolution = filePicker.getMediaResolution(mediaFileInfo.uri)
                val isVideo = mediaFileInfo.mimeType?.startsWith("video/") == true
                val durationMs = if (isVideo) filePicker.getVideoDuration(mediaFileInfo.uri)?.let { it * 1000 } else null
                val thumbnailPath = localPath?.let { thumbnailGenerator.generateThumbnail(it, isVideo) }
                val media = Media(
                    fileHash = fileHash,
                    localMediaPath = localPath,
                    localThumbnailPath = thumbnailPath,
                    mimeType = mediaFileInfo.mimeType,
                    fileSize = mediaFileInfo.size,
                    width = resolution?.split("x")?.getOrNull(0)?.toIntOrNull(),
                    height = resolution?.split("x")?.getOrNull(1)?.toIntOrNull(),
                    durationMs = durationMs
                )
                val mediaId = databaseManager.mediaRepository.insertMedia(media)
                messageRepository.addMediaToMessage(localMessageId, mediaId, position = index)
                initialStates.add(MediaUploadState(
                    mediaFileInfo = mediaFileInfo,
                    localMediaId = mediaId,
                    localFilePath = localPath
                ))
            }

            // 注册到 _sendingMessages
            _sendingMessages.update { it + (tempId to SendingMessage(
                tempId = tempId,
                localMessageId = localMessageId,
                text = text.ifBlank { null },
                actorId = null,
                mediaStates = initialStates,
                status = SendStatus.UPLOADING
            )) }

            // Step 2: 并行上传所有媒体
            try {
                val uploadedStates = coroutineScope {
                    initialStates.mapIndexed { idx, state ->
                        async { uploadWithProgress(tempId, idx, state) }
                    }.awaitAll()
                }

                val failedCount = uploadedStates.count { it.error != null }
                if (failedCount > 0) {
                    messageRepository.updateSendStatus(localMessageId, Message.MSG_STATUS_FAILED)
                    _sendingMessages.update { map ->
                        val c = map[tempId] ?: return@update map
                        map + (tempId to c.copy(status = SendStatus.FAILED, error = "上传失败 $failedCount 个文件", mediaStates = uploadedStates))
                    }
                    onError("上传失败 $failedCount 个文件")
                    return@launch
                }

                // Step 3: POST /messages 创建消息
                _sendingMessages.update { map ->
                    val c = map[tempId] ?: return@update map
                    map + (tempId to c.copy(status = SendStatus.CREATING, mediaStates = uploadedStates))
                }

                val serverMessage = SyncNetwork.createMessageService.createMessage(
                    CreateMessageRequest(
                        text = text.ifBlank { null },
                        actor_id = null,
                        files = uploadedStates.mapNotNull { it.serverPath }
                    )
                )

                // Step 4: 替换本地临时 ID
                messageRepository.replaceWithServerId(localMessageId, serverMessage)

                // Step 5: 清除发送中状态
                _sendingMessages.update { it - tempId }
                onSuccess()
            } catch (e: Exception) {
                Log.e(TAG, "sendMessage 失败: ${e.message}", e)
                messageRepository.updateSendStatus(localMessageId, Message.MSG_STATUS_FAILED)
                _sendingMessages.update { map ->
                    val c = map[tempId] ?: return@update map
                    map + (tempId to c.copy(status = SendStatus.FAILED, error = e.message))
                }
                onError("发送失败: ${e.message}")
            }
        }
    }

    /** 上传单个媒体文件并实时回报进度 */
    private suspend fun uploadWithProgress(
        tempId: String,
        mediaIndex: Int,
        state: MediaUploadState
    ): MediaUploadState {
        val filePath = state.localFilePath ?: return state.copy(error = "文件路径为空")
        val file = File(filePath)
        if (!file.exists()) return state.copy(error = "文件不存在: $filePath")

        return try {
            val mimeType = state.mediaFileInfo.mimeType ?: "application/octet-stream"
            val progressBody = ProgressRequestBody(file, mimeType) { progress ->
                val map = _sendingMessages.value
                val current = map[tempId] ?: return@ProgressRequestBody
                val updatedStates = current.mediaStates.toMutableList()
                if (mediaIndex < updatedStates.size) {
                    updatedStates[mediaIndex] = updatedStates[mediaIndex].copy(uploadProgress = progress)
                    _sendingMessages.value = map + (tempId to current.copy(mediaStates = updatedStates))
                }
            }
            val filePart = MultipartBody.Part.createFormData(
                name = "file",
                filename = state.mediaFileInfo.fileName,
                body = progressBody
            )
            val response = SyncNetwork.uploadService.uploadMedia(filePart)
            state.copy(serverPath = response.path, uploadProgress = 1f, error = null)
        } catch (e: Exception) {
            Log.e(TAG, "uploadMedia 失败 [${state.mediaFileInfo.fileName}]: ${e.message}", e)
            state.copy(error = e.message)
        }
    }

    /**
     * 重试发送失败的消息（只重传 serverPath == null 的媒体）
     */
    fun retryMessage(tempId: String) {
        val sending = _sendingMessages.value[tempId] ?: return
        viewModelScope.launch {
            _sendingMessages.update { map ->
                map + (tempId to sending.copy(status = SendStatus.UPLOADING, error = null))
            }
            try {
                val uploadedStates = coroutineScope {
                    sending.mediaStates.mapIndexed { idx, state ->
                        async {
                            if (state.serverPath == null) uploadWithProgress(tempId, idx, state) else state
                        }
                    }.awaitAll()
                }

                val failedCount = uploadedStates.count { it.error != null }
                if (failedCount > 0) {
                    _sendingMessages.update { map ->
                        val c = map[tempId] ?: return@update map
                        map + (tempId to c.copy(status = SendStatus.FAILED, error = "上传失败 $failedCount 个文件", mediaStates = uploadedStates))
                    }
                    return@launch
                }

                _sendingMessages.update { map ->
                    val c = map[tempId] ?: return@update map
                    map + (tempId to c.copy(status = SendStatus.CREATING, mediaStates = uploadedStates))
                }

                val serverMessage = SyncNetwork.createMessageService.createMessage(
                    CreateMessageRequest(
                        text = sending.text,
                        actor_id = sending.actorId,
                        files = uploadedStates.mapNotNull { it.serverPath }
                    )
                )
                messageRepository.replaceWithServerId(sending.localMessageId, serverMessage)
                _sendingMessages.update { it - tempId }
            } catch (e: Exception) {
                Log.e(TAG, "retryMessage 失败: ${e.message}", e)
                messageRepository.updateSendStatus(sending.localMessageId, Message.MSG_STATUS_FAILED)
                _sendingMessages.update { map ->
                    val c = map[tempId] ?: return@update map
                    map + (tempId to c.copy(status = SendStatus.FAILED, error = e.message))
                }
            }
        }
    }

    /**
     * 取消发送中的消息（删除本地临时记录）
     */
    fun cancelSending(tempId: String) {
        val sending = _sendingMessages.value[tempId] ?: return
        viewModelScope.launch {
            messageRepository.deleteMessage(sending.localMessageId)
            _sendingMessages.update { it - tempId }
        }
    }

    private suspend fun parseAndAttachTags(text: String, messageId: Long, databaseManager: DatabaseManager) {
        messageRepository.parseAndAttachTags(text, messageId, databaseManager.tagRepository)
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
