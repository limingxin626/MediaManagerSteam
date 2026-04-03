package com.example.myapplication.ui.viewmodel

import android.content.Context
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
import com.example.myapplication.data.repository.MessageRepository
import com.example.myapplication.utils.MediaFileInfo
import com.example.myapplication.utils.MediaFilePicker
import com.example.myapplication.utils.ThumbnailGenerator
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.launch

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

    /**
     * 搜索消息
     */
    fun searchMessages(query: String) {
        _searchQuery.value = query
    }

    /**
     * 清除搜索
     */
    fun clearSearch() {
        _searchQuery.value = ""
    }

    /**
     * 设置标签过滤
     */
    fun setTagId(tagId: Long?) {
        _tagId.value = tagId
    }

    /**
     * 设置演员过滤
     */
    fun setActorId(actorId: Long?) {
        _actorId.value = actorId
    }

    /**
     * 刷新消息列表
     */
    fun refreshMessages() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                // 这里可以添加刷新逻辑
                _uiState.value = _uiState.value.copy(isLoading = false)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "刷新失败: ${e.message}"
                )
            }
        }
    }

    /**
     * 清除错误
     */
    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    /**
     * 清除消息
     */
    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null)
    }

    /**
     * 切换消息收藏状态
     */
    fun toggleStarred(messageId: Long) {
        viewModelScope.launch {
            try {
                messageRepository.toggleStarred(messageId)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = "操作失败: ${e.message}")
            }
        }
    }

    /**
     * 删除消息
     */
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
            try {
                val message = Message(text = text.ifBlank { null })
                val messageId = messageRepository.createMessage(message)

                // 解析文本中的 #tag 并关联到消息
                parseAndAttachTags(text, messageId, databaseManager)

                val filePicker = MediaFilePicker(context)
                val thumbnailGenerator = ThumbnailGenerator(context)
                mediaList.forEachIndexed { index, mediaFileInfo ->
                    val localPath = filePicker.copyFileToAppStorage(
                        mediaFileInfo.uri,
                        mediaFileInfo.fileName
                    )
                    val fileHash = filePicker.computeBlake2bHash(mediaFileInfo.uri)
                        ?: mediaFileInfo.uri.toString()
                    val resolution = filePicker.getMediaResolution(mediaFileInfo.uri)
                    val width = resolution?.split("x")?.getOrNull(0)?.toIntOrNull()
                    val height = resolution?.split("x")?.getOrNull(1)?.toIntOrNull()
                    val isVideo = mediaFileInfo.mimeType?.startsWith("video/") == true
                    val durationMs = if (isVideo) {
                        filePicker.getVideoDuration(mediaFileInfo.uri)?.let { it * 1000 }
                    } else null
                    val thumbnailPath = localPath?.let {
                        thumbnailGenerator.generateThumbnail(it, isVideo)
                    }

                    val media = Media(
                        fileHash = fileHash,
                        localMediaPath = localPath,
                        localThumbnailPath = thumbnailPath,
                        mimeType = mediaFileInfo.mimeType,
                        fileSize = mediaFileInfo.size,
                        width = width,
                        height = height,
                        durationMs = durationMs
                    )
                    val mediaId = databaseManager.mediaRepository.insertMedia(media)
                    messageRepository.addMediaToMessage(messageId, mediaId, position = index)
                }

                onSuccess()
            } catch (e: Exception) {
                onError("发送失败: ${e.message}")
            }
        }
    }

    /**
     * 从文本中解析 #tag 并关联到消息
     */
    private suspend fun parseAndAttachTags(
        text: String,
        messageId: Long,
        databaseManager: DatabaseManager
    ) {
        messageRepository.parseAndAttachTags(text, messageId, databaseManager.tagRepository)
    }

    companion object
}

/**
 * UI状态
 */
data class UIState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null
)
