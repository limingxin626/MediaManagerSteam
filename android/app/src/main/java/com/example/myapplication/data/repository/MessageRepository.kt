package com.example.myapplication.data.repository

import android.util.Log
import com.example.myapplication.data.database.dao.ActorDao
import com.example.myapplication.data.database.dao.MediaDao
import com.example.myapplication.data.database.dao.MessageDao
import com.example.myapplication.data.database.dao.TagDao
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.Message
import com.example.myapplication.data.database.entities.MessageMedia
import com.example.myapplication.data.database.entities.MessageTag
import com.example.myapplication.data.database.entities.MessageWithDetails
import com.example.myapplication.data.database.entities.SyncOutboxItem
import com.example.myapplication.data.database.entities.Tag
import com.example.myapplication.data.model.MessageSortBy
import com.example.myapplication.data.model.SyncResult
import com.example.myapplication.data.service.SyncConfig
import com.example.myapplication.data.service.SyncNetwork
import com.example.myapplication.data.service.buildFullUrl
import androidx.paging.PagingSource
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import com.google.gson.Gson
import java.time.LocalDateTime
import java.time.ZoneOffset

/**
 * 消息仓库
 */
class MessageRepository(
    private val messageDao: MessageDao,
    private val mediaDao: MediaDao,
    private val tagDao: TagDao,
    private val actorDao: ActorDao,
    private val outboxRepository: SyncOutboxRepository? = null
) {

    /**
     * 解析文本中的 #tag 并关联到消息
     */
    suspend fun parseAndAttachTags(text: String, messageId: Long, tagRepository: TagRepository) {
        if (text.isBlank()) return
        val tagNames = TAG_PATTERN.findAll(text)
            .map { it.groupValues[1] }
            .distinct()
            .toList()
        if (tagNames.isEmpty()) return

        for (name in tagNames) {
            val tag = tagRepository.createOrGetTag(name)
            addTagToMessage(messageId, tag.id)
        }
    }
    
    /**
     * 获取消息列表（响应式 Flow）
     */
    fun getMessages(query: String, sortBy: MessageSortBy): Flow<List<Message>> {
        if (query.isBlank()) {
            return when (sortBy) {
                MessageSortBy.CREATED_DESC -> messageDao.getAllMessages()
                MessageSortBy.CREATED_ASC -> messageDao.getAllMessagesAsc()
                MessageSortBy.STARRED_FIRST -> messageDao.getAllMessagesStarredFirst()
            }
        }
        return messageDao.searchMessages(query)
    }
    
    /**
     * 获取分页消息列表（含详情）
     */
    fun getMessagesPaged(query: String): PagingSource<Int, MessageWithDetails> {
        return if (query.isBlank()) {
            messageDao.getMessagesPaged()
        } else {
            messageDao.searchMessagesPaged(query)
        }
    }

    /**
     * 获取按标签过滤的分页消息列表
     */
    fun getMessagesByTagPaged(tagId: Long, query: String): PagingSource<Int, MessageWithDetails> {
        return if (query.isBlank()) {
            messageDao.getMessagesByTagPaged(tagId)
        } else {
            messageDao.searchMessagesByTagPaged(tagId, query)
        }
    }

    /**
     * 获取标签的最新消息（用于 group 预览）
     */
    suspend fun getLastMessageForTag(tagId: Long): MessageWithDetails? {
        return messageDao.getLastMessageForTag(tagId)
    }

    /**
     * 获取消息总数
     */
    suspend fun getTotalMessageCount(): Int {
        return messageDao.getTotalMessageCount()
    }

    /**
     * 获取最新一条消息（用于"全部" group 预览）
     */
    suspend fun getLastMessage(): MessageWithDetails? {
        return messageDao.getLastMessage()
    }

    /**
     * 根据ID获取消息
     */
    suspend fun getMessageById(id: Long): Message? {
        return messageDao.getMessageById(id)
    }

    /**
     * 获取消息完整信息（含媒体、标签、演员）
     */
    suspend fun getMessageWithDetails(id: Long): MessageWithDetails? {
        return messageDao.getMessageWithDetails(id)
    }

    /**
     * 获取所有消息完整信息（响应式 Flow）
     */
    fun getAllMessagesWithDetails(): Flow<List<MessageWithDetails>> {
        return messageDao.getAllMessagesWithDetails()
    }
    
    /**
     * 创建消息
     */
    suspend fun createMessage(message: Message): Long {
        val insertedId = messageDao.insertMessage(message)

        if (insertedId > 0) {
            val payload = message.copy(id = insertedId)
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_MESSAGE,
                entityId = insertedId,
                payloadJson = Gson().toJson(payload)
            )
        }

        return insertedId
    }
    
    /**
     * 更新消息
     */
    suspend fun updateMessage(message: Message) {
        val updatedMessage = message.copy(updatedAt = System.currentTimeMillis())
        messageDao.updateMessage(updatedMessage)

        if (updatedMessage.id > 0) {
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_MESSAGE,
                entityId = updatedMessage.id,
                payloadJson = Gson().toJson(updatedMessage)
            )
        }
    }
    
    /**
     * 删除消息
     */
    suspend fun deleteMessage(messageId: Long) {
        // CASCADE handles junction table cleanup automatically
        messageDao.deleteMessage(messageId)

        if (messageId > 0) {
            outboxRepository?.enqueueDelete(
                entityType = SyncOutboxItem.ENTITY_MESSAGE,
                entityId = messageId
            )
        }
    }
    
    /**
     * 切换消息收藏状态
     */
    suspend fun toggleStarred(messageId: Long) {
        val message = messageDao.getMessageById(messageId)
        message?.let {
            val updated = it.copy(
                starred = !it.starred,
                updatedAt = System.currentTimeMillis()
            )
            messageDao.updateMessage(updated)

            if (updated.id > 0) {
                outboxRepository?.enqueueUpsert(
                    entityType = SyncOutboxItem.ENTITY_MESSAGE,
                    entityId = updated.id,
                    payloadJson = Gson().toJson(updated)
                )
            }
        }
    }
    
    /**
     * 添加媒体到消息
     */
    suspend fun addMediaToMessage(messageId: Long, mediaId: Long, position: Int) {
        val messageMedia = MessageMedia(
            messageId = messageId,
            mediaId = mediaId,
            position = position
        )
        messageDao.insertMessageMedia(messageMedia)
    }
    
    /**
     * 添加标签到消息
     */
    suspend fun addTagToMessage(messageId: Long, tagId: Long) {
        val messageTag = MessageTag(
            messageId = messageId,
            tagId = tagId
        )
        messageDao.insertMessageTag(messageTag)
    }

    /**
     * 移除消息的标签
     */
    suspend fun removeTagFromMessage(messageId: Long, tagId: Long) {
        messageDao.deleteMessageTag(messageId, tagId)
    }
    
    /**
     * 获取消息的媒体列表
     */
    suspend fun getMessageMedia(messageId: Long): List<MessageMedia> {
        return messageDao.getMessageMediaByMessageId(messageId)
    }

    /**
     * 获取消息的媒体对象列表
     */
    suspend fun getMediaByMessageId(messageId: Long): List<Media> {
        return messageDao.getMediaByMessageId(messageId)
    }
    
    /**
     * 获取消息的标签ID列表
     */
    suspend fun getMessageTagIds(messageId: Long): List<Long> {
        return messageDao.getMessageTagIdsByMessageId(messageId)
    }

    /**
     * 获取消息的标签对象列表
     */
    suspend fun getTagsByMessageId(messageId: Long): List<Tag> {
        return messageDao.getTagsByMessageId(messageId)
    }

    /**
     * 获取消息的标签（响应式 Flow）
     */
    fun getTagsByMessageIdFlow(messageId: Long): Flow<List<Tag>> {
        return messageDao.getTagsByMessageIdFlow(messageId)
    }

    /**
     * 删除消息的所有媒体关联
     */
    suspend fun deleteMessageMediaByMessageId(messageId: Long) {
        messageDao.deleteMessageMediaByMessageId(messageId)
    }

    /**
     * 删除消息的所有标签关联
     */
    suspend fun deleteMessageTagsByMessageId(messageId: Long) {
        messageDao.deleteMessageTagsByMessageId(messageId)
    }

    // ==================== 远程同步 ====================

    private val syncService by lazy { SyncNetwork.syncService }

    /**
     * 从远程服务器同步消息数据（upsert，不删除本地多余数据）。
     * 插入顺序: Tag → Media → Message → MessageMedia + MessageTag
     */
    suspend fun syncFromRemote(): SyncResult = withContext(Dispatchers.IO) {
        return@withContext try {
            Log.d(TAG, "开始从远程服务器同步消息数据...")

            val remoteMessages = syncService.getMessages()
            Log.d(TAG, "获取到 ${remoteMessages.size} 条远程消息数据")

            val existingIds = messageDao.getAllMessageIdsSync().toSet()
            val validActorIds = actorDao.getAllActorIdsSync().toSet()
            var insertedCount = 0
            var updatedCount = 0

            for (remote in remoteMessages) {
                try {
                    // 1) Upsert Tags
                    for (rt in remote.tags) {
                        val tag = Tag(
                            id = rt.id,
                            name = rt.name,
                            category = rt.category,
                        )
                        tagDao.insertTag(tag)
                    }

                    // 2) Upsert Media (IGNORE + update 避免 REPLACE 级联删除 message_media)
                    for (rm in remote.media_items) {
                        val media = Media(
                            id = rm.id,
                            remoteMediaUrl = buildFullUrl(SyncConfig.BASE_URL, rm.file_url),
                            remoteThumbnailUrl = buildFullUrl(SyncConfig.BASE_URL, rm.thumb_url),
                            fileHash = rm.file_hash ?: "unknown_${rm.id}",
                            fileSize = rm.file_size,
                            mimeType = rm.mime_type,
                            width = rm.width,
                            height = rm.height,
                            durationMs = rm.duration?.toLong()?.times(1000),
                            rating = rm.rating,
                            starred = rm.starred,
                        )
                        val insertedId = mediaDao.insertMediaIgnore(media)
                        if (insertedId == -1L) {
                            // 已存在，更新元数据
                            mediaDao.updateMedia(media)
                        }
                    }

                    // 3) Upsert Message
                    val createdAtMs = try {
                        LocalDateTime.parse(remote.created_at).toInstant(ZoneOffset.UTC).toEpochMilli()
                    } catch (_: Exception) {
                        System.currentTimeMillis()
                    }
                    val updatedAtMs = try {
                        LocalDateTime.parse(remote.updated_at).toInstant(ZoneOffset.UTC).toEpochMilli()
                    } catch (_: Exception) {
                        System.currentTimeMillis()
                    }

                    val safeActorId = if (remote.actor_id != null && remote.actor_id in validActorIds) remote.actor_id else null

                    val message = Message(
                        id = remote.id,
                        text = remote.text,
                        actorId = safeActorId,
                        starred = remote.starred,
                        createdAt = createdAtMs,
                        updatedAt = updatedAtMs,
                    )
                    messageDao.insertMessage(message)

                    // 4) Link MessageMedia (clear + re-insert)
                    messageDao.deleteMessageMediaByMessageId(remote.id)
                    for (rm in remote.media_items) {
                        messageDao.insertMessageMedia(
                            MessageMedia(
                                messageId = remote.id,
                                mediaId = rm.id,
                                position = rm.position,
                            )
                        )
                    }

                    // 5) Link MessageTag (clear + re-insert)
                    messageDao.deleteMessageTagsByMessageId(remote.id)
                    for (rt in remote.tags) {
                        messageDao.insertMessageTag(
                            MessageTag(messageId = remote.id, tagId = rt.id)
                        )
                    }

                    if (remote.id in existingIds) updatedCount++ else insertedCount++
                } catch (e: Exception) {
                    Log.e(TAG, "同步消息 id=${remote.id} 失败, actorId=${remote.actor_id}, " +
                            "mediaIds=${remote.media_items.map { it.id }}, " +
                            "tagIds=${remote.tags.map { it.id }}: ${e.message}")
                    throw e
                }
            }

            Log.d(TAG, "消息同步完成：新增 $insertedCount 条，更新 $updatedCount 条")
            SyncResult.Success(insertedCount, updatedCount)
        } catch (e: Exception) {
            Log.e(TAG, "消息同步失败: ${e.message}", e)
            SyncResult.Error(e.message ?: "未知错误")
        }
    }

    companion object {
        private const val TAG = "MessageRepository"
        val TAG_PATTERN = Regex("""#([\w\u4e00-\u9fff\u3400-\u4dbf-]+)""")
    }
}
