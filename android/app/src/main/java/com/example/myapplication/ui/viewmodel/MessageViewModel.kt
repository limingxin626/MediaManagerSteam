package com.example.myapplication.ui.viewmodel

import android.content.Context
import android.net.Uri
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.Pager
import androidx.paging.PagingConfig
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.Message
import com.example.myapplication.data.database.entities.MessageWithDetails
import com.example.myapplication.data.model.ProgressRequestBody
import com.example.myapplication.data.model.SystemMedia
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
import java.io.IOException
import okhttp3.MultipartBody
import java.io.File
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

/**
 * 消息视图模型
 */
class MessageViewModel(
    private val messageRepository: MessageRepository,
    context: Context
) : ViewModel() {
    private val appContext = context.applicationContext
    // 搜索查询
    private val _searchQuery = MutableStateFlow("")
    val searchQuery = _searchQuery.asStateFlow()

    // 发送中状态（文件预处理 + DB 事务完成前为 true）
    private val _isSending = MutableStateFlow(false)
    val isSending = _isSending.asStateFlow()

    // 标签过滤
    private val _tagId = MutableStateFlow<Long?>(null)
    val tagId: StateFlow<Long?> = _tagId.asStateFlow()

    // 合集过滤
    private val _collectionId = MutableStateFlow<Long?>(null)
    val collectionId: StateFlow<Long?> = _collectionId.asStateFlow()

    // 分页消息列表
    @OptIn(ExperimentalCoroutinesApi::class)
    val messagesPaged: Flow<PagingData<MessageWithDetails>> =
        combine(_searchQuery, _tagId, _collectionId) { query, tagId, collectionId ->
            Triple(query, tagId, collectionId)
        }.flatMapLatest { (query, tagId, collectionId) ->
            Pager(
                config = PagingConfig(pageSize = 30, prefetchDistance = 10),
                pagingSourceFactory = {
                    when {
                        collectionId != null -> messageRepository.getMessagesByCollectionPaged(collectionId, query)
                        tagId != null -> messageRepository.getMessagesByTagPaged(tagId, query)
                        else -> messageRepository.getMessagesPaged(query)
                    }
                }
            ).flow
        }.cachedIn(viewModelScope)

    // UI状态
    private val _uiState = MutableStateFlow(UIState())
    val uiState: StateFlow<UIState> = _uiState.asStateFlow()

    fun searchMessages(query: String) {
        _searchQuery.value = query
    }

    fun clearSearch() {
        _searchQuery.value = ""
    }

    fun setTagId(tagId: Long?) {
        _tagId.value = tagId
    }

    fun setCollectionId(collectionId: Long?) {
        _collectionId.value = collectionId
    }

    fun refreshMessages() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null)
    }

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
     *
     * @param splitPerMedia true 时每个媒体各自组成一条消息（文本只挂在第一条）
     */
    fun sendMessage(
        text: String,
        mediaList: List<MediaFileInfo>,
        tagIds: List<Long>,
        context: Context,
        onSuccess: () -> Unit,
        onError: (String) -> Unit,
        splitPerMedia: Boolean = false
    ) {
        if (splitPerMedia && mediaList.size > 1) {
            sendSplitMessages(text, mediaList, tagIds, context)
            return
        }
        viewModelScope.launch {
            _isSending.value = true
            val filePicker = MediaFilePicker(context)
            val thumbnailGenerator = ThumbnailGenerator(context)

            // Step 1: 在主线程外预处理所有媒体文件（复制、哈希、缩略图）
            data class PreparedMedia(
                val info: MediaFileInfo,
                val localPath: String?,
                val entity: Media
            )

            val preparedList = withContext(Dispatchers.IO) {
                mediaList.map { mediaFileInfo ->
                    val entity = prepareMedia(mediaFileInfo, filePicker, thumbnailGenerator)
                    PreparedMedia(
                        info = mediaFileInfo,
                        localPath = entity.localMediaPath,
                        entity = entity
                    )
                }
            }

            // Step 2: 单事务写入 Message + 所有 Media + junctions + tags → PagingData 只刷新一次
            val (localMessageId, mediaIds) = messageRepository.createMessageWithMedia(
                message = Message(
                    text = text.ifBlank { null },
                    sendStatus = Message.MSG_STATUS_PUSHING
                ),
                mediaEntities = preparedList.map { it.entity },
                tagIds = tagIds
            )
            // ↑ 至此消息已在 paging 中完整可见（带全部本地缩略图）
            _isSending.value = false

            // Step 3: 后台上传 + 推送（失败则留 PENDING_SYNC，等用户手动同步）
            try {
                val uploadResults = coroutineScope {
                    preparedList.mapIndexed { index, prepared ->
                        async {
                            val serverPath = uploadFile(prepared.info, prepared.localPath)
                            if (serverPath != null) ClientMediaFile(
                                id = mediaIds[index],
                                file_path = serverPath
                            ) else null
                        }
                    }.awaitAll()
                }
                if (uploadResults.any { it == null } && preparedList.isNotEmpty()) {
                    Log.w(TAG, "sendMessage 部分文件上传失败，标记为待同步")
                    messageRepository.updateSendStatus(
                        localMessageId,
                        Message.MSG_STATUS_PENDING_SYNC
                    )
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
                        collection_id = null,
                        tag_ids = tagIds,
                        created_at = createdAtIso,
                        files = uploadResults.filterNotNull()
                    )
                )

                messageRepository.applyRemoteUrls(localMessageId, response)
                onSuccess()
            } catch (e: IOException) {
                Log.w(TAG, "sendMessage 网络异常，标记 PENDING_SYNC 等待手动重试: ${e.message}")
                messageRepository.updateSendStatus(localMessageId, Message.MSG_STATUS_PENDING_SYNC)
            } catch (e: Exception) {
                Log.e(TAG, "sendMessage 同步失败（业务异常）: ${e.message}", e)
                messageRepository.updateSendStatus(localMessageId, Message.MSG_STATUS_PUSH_FAILED)
            }
        }
    }

    /**
     * 直接引用 MediaStore 项创建一条消息，不复制原文件。
     */
    fun sendSystemMediaMessage(
        systemMedia: List<SystemMedia>,
        onLocalCreated: () -> Unit = {},
        onError: (String) -> Unit = {}
    ) {
        if (systemMedia.isEmpty() || _isSending.value) return
        viewModelScope.launch {
            _isSending.value = true
            var createdMessageId: Long? = null
            try {
                val filePicker = MediaFilePicker(appContext)
                val entities = withContext(Dispatchers.IO) {
                    systemMedia.map { item ->
                        val hash = filePicker.computeBlake2bHash(item.uri)
                            ?: throw SourceMediaUnavailableException(item.displayName)
                        Media(
                            sourceType = Media.SOURCE_MEDIA_STORE,
                            contentUri = item.uri.toString(),
                            originalFileName = item.displayName,
                            fileHash = hash,
                            fileSize = item.size,
                            mimeType = item.mimeType,
                            width = item.width.takeIf { it > 0 },
                            height = item.height.takeIf { it > 0 },
                            durationMs = item.duration
                        )
                    }
                }
                val (messageId, _) = messageRepository.createMessageWithMedia(
                    message = Message(sendStatus = Message.MSG_STATUS_PUSHING),
                    mediaEntities = entities
                )
                createdMessageId = messageId
                _isSending.value = false
                onLocalCreated()

                val storedMedia = messageRepository.getMediaByMessageId(messageId)
                val uploadResults = coroutineScope {
                    storedMedia.map { media ->
                        async {
                            ClientMediaFile(
                                id = media.id,
                                file_path = uploadFileFromMedia(media)
                            )
                        }
                    }.awaitAll()
                }
                val message = messageRepository.getMessageById(messageId)
                val createdAtIso = message?.let {
                    Instant.ofEpochMilli(it.createdAt)
                        .atOffset(ZoneOffset.UTC)
                        .format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                }
                val response = SyncNetwork.messageSyncService.createFromClient(
                    MessageSyncRequest(
                        id = messageId,
                        text = null,
                        collection_id = null,
                        tag_ids = emptyList(),
                        created_at = createdAtIso,
                        files = uploadResults
                    )
                )
                messageRepository.applyRemoteUrls(messageId, response)
            } catch (e: SourceMediaUnavailableException) {
                _isSending.value = false
                createdMessageId?.let {
                    messageRepository.updateSendStatus(it, Message.MSG_STATUS_PUSH_FAILED)
                }
                onError("原始媒体不可用: ${e.fileName}")
            } catch (e: IOException) {
                _isSending.value = false
                createdMessageId?.let {
                    messageRepository.updateSendStatus(it, Message.MSG_STATUS_PENDING_SYNC)
                }
                onError("网络连接失败，消息已保存并可稍后重试")
            } catch (e: Exception) {
                _isSending.value = false
                createdMessageId?.let {
                    messageRepository.updateSendStatus(it, Message.MSG_STATUS_PUSH_FAILED)
                }
                Log.e(TAG, "创建系统媒体消息失败", e)
                onError("创建消息失败: ${e.message ?: "未知错误"}")
            }
        }
    }

    /**
     * 拆分发送：每个媒体各自组成一条消息（文本只挂在第一条）。
     * 先把 N 条消息全部落库（立刻在 paging 中可见），再逐条走 retrySync 上传推送。
     */
    private fun sendSplitMessages(
        text: String,
        mediaList: List<MediaFileInfo>,
        tagIds: List<Long>,
        context: Context
    ) {
        viewModelScope.launch {
            _isSending.value = true
            val filePicker = MediaFilePicker(context)
            val thumbnailGenerator = ThumbnailGenerator(context)

            val entities = withContext(Dispatchers.IO) {
                mediaList.map { info -> prepareMedia(info, filePicker, thumbnailGenerator) }
            }

            val messageIds = entities.mapIndexed { index, entity ->
                val (id, _) = messageRepository.createMessageWithMedia(
                    message = Message(
                        text = if (index == 0) text.ifBlank { null } else null,
                        sendStatus = Message.MSG_STATUS_PUSHING
                    ),
                    mediaEntities = listOf(entity),
                    tagIds = tagIds
                )
                id
            }
            _isSending.value = false

            messageIds.forEach { retrySync(it) }
        }
    }

    /**
     * 预处理单个媒体文件：复制到应用存储、计算哈希、生成缩略图。必须在 IO 线程调用。
     */
    private suspend fun prepareMedia(
        info: MediaFileInfo,
        filePicker: MediaFilePicker,
        thumbnailGenerator: ThumbnailGenerator
    ): Media {
        val localPath = filePicker.copyFileToAppStorage(info.uri, info.fileName)
        val fileHash = filePicker.computeBlake2bHash(info.uri) ?: info.uri.toString()
        val resolution = filePicker.getMediaResolution(info.uri)
        val isVideo = info.mimeType?.startsWith("video/") == true
        val durationMs =
            if (isVideo) filePicker.getVideoDuration(info.uri)?.let { it * 1000 } else null
        val thumbnailPath = localPath?.let { thumbnailGenerator.generateThumbnail(it, isVideo) }
        return Media(
            sourceType = Media.SOURCE_APP_FILE,
            originalFileName = info.fileName,
            fileHash = fileHash,
            localMediaPath = localPath,
            localThumbnailPath = thumbnailPath,
            mimeType = info.mimeType,
            fileSize = info.size,
            width = resolution?.split("x")?.getOrNull(0)?.toIntOrNull(),
            height = resolution?.split("x")?.getOrNull(1)?.toIntOrNull(),
            durationMs = durationMs
        )
    }

    /**
     * 重试推送失败的消息（重新上传所有本地媒体并调用 create-from-client）
     */
    fun retrySync(messageId: Long) {
        viewModelScope.launch {
            messageRepository.updateSendStatus(messageId, Message.MSG_STATUS_PUSHING)
            try {
                val mediaList = messageRepository.getMediaByMessageId(messageId)
                val tagIds = messageRepository.getMessageTagIds(messageId)
                val uploadResults = coroutineScope {
                    mediaList.map { media ->
                        async {
                            ClientMediaFile(
                                id = media.id,
                                file_path = uploadFileFromMedia(media)
                            )
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
                        collection_id = msg?.collectionId,
                        tag_ids = tagIds,
                        created_at = createdAtIso,
                        files = uploadResults
                    )
                )
                messageRepository.applyRemoteUrls(messageId, response)
            } catch (e: SourceMediaUnavailableException) {
                Log.w(TAG, "retrySync 原始媒体不可用: ${e.fileName}")
                messageRepository.updateSendStatus(messageId, Message.MSG_STATUS_PUSH_FAILED)
            } catch (e: IOException) {
                Log.w(TAG, "retrySync 网络异常，回到 PENDING_SYNC: ${e.message}")
                messageRepository.updateSendStatus(messageId, Message.MSG_STATUS_PENDING_SYNC)
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
            val body =
                ProgressRequestBody(file, mediaFileInfo.mimeType ?: "application/octet-stream") { }
            val part = MultipartBody.Part.createFormData("file", mediaFileInfo.fileName, body)
            SyncNetwork.uploadService.uploadMedia(part).path
        } catch (e: Exception) {
            Log.e(TAG, "uploadFile 失败 [${mediaFileInfo.fileName}]: ${e.message}", e)
            null
        }
    }

    /** 从已有 Media 实体上传文件 */
    private suspend fun uploadFileFromMedia(media: Media): String {
        val mimeType = media.mimeType ?: "application/octet-stream"
        val localPath = media.localMediaPath
        val body: ProgressRequestBody
        val fileName: String

        if (localPath != null) {
            val file = File(localPath)
            if (!file.exists()) throw SourceMediaUnavailableException(file.name)
            body = ProgressRequestBody(file, mimeType) { }
            fileName = media.originalFileName ?: file.name
        } else {
            val uriString = media.contentUri
                ?: throw SourceMediaUnavailableException(media.originalFileName ?: media.id.toString())
            val uri = Uri.parse(uriString)
            fileName = media.originalFileName ?: "media_${media.id}"
            body = ProgressRequestBody(
                openStream = {
                    appContext.contentResolver.openInputStream(uri)
                        ?: throw SourceMediaUnavailableException(fileName)
                },
                length = media.fileSize ?: -1L,
                mimeType = mimeType,
                onProgress = { }
            )
        }

        return SyncNetwork.uploadService.uploadMedia(
            MultipartBody.Part.createFormData("file", fileName, body)
        ).path
    }

    private class SourceMediaUnavailableException(val fileName: String) : IOException(fileName)

    companion object {
        private const val TAG = "MessageViewModel"
    }
}

data class UIState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null
)
