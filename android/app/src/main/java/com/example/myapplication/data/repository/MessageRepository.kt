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
     * 获取按演员过滤的分页消息列表
     */
    fun getMessagesByActorPaged(actorId: Long, query: String): PagingSource<Int, MessageWithDetails> {
        return if (query.isBlank()) {
            messageDao.getMessagesByActorPaged(actorId)
        } else {
            messageDao.searchMessagesByActorPaged(actorId, query)
        }
    }

    /**
     * 获取指定演员的消息数量
     */
    suspend fun getMessageCountByActor(actorId: Long): Int {
        return messageDao.getMessageCountByActor(actorId)
    }

    /**
     * 获取指定演员的最新消息（用于 group 预览）
     */
    suspend fun getLastMessageByActor(actorId: Long): MessageWithDetails? {
        return messageDao.getLastMessageByActor(actorId)
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

    /**
     * 增量同步：拉取 since 之后的变更日志并应用到本地。
     * - 410 响应 → 返回 SyncResult.NeedFullSync，调用方应回退到 syncFromRemote()
     * - has_more=true → 递归拉取直到完成
     */
    suspend fun syncIncremental(since: String): SyncResult = withContext(Dispatchers.IO) {
        var cursor = since
        var totalInserted = 0
        var totalUpdated = 0
        var totalDeleted = 0

        while (true) {
            val response = try {
                syncService.getChanges(since = cursor)
            } catch (e: Exception) {
                Log.e(TAG, "增量同步网络请求失败: ${e.message}", e)
                return@withContext SyncResult.Error(e.message ?: "网络错误")
            }

            // 410 → 需要全量同步
            if (response.code() == 410) {
                Log.w(TAG, "增量同步返回 410，需要全量同步")
                return@withContext SyncResult.NeedFullSync
            }

            if (!response.isSuccessful) {
                return@withContext SyncResult.Error("服务器返回 ${response.code()}")
            }

            val body = response.body() ?: return@withContext SyncResult.Error("响应体为空")
            val validActorIds = actorDao.getAllActorIdsSync().toSet()

            for (change in body.changes) {
                try {
                    when (change.operation.uppercase()) {
                        "DELETE" -> {
                            when (change.entity_type.uppercase()) {
                                "MESSAGE" -> {
                                    messageDao.deleteMessageTagsByMessageId(change.entity_id)
                                    messageDao.deleteMessageMediaByMessageId(change.entity_id)
                                    messageDao.deleteMessage(change.entity_id)
                                }
                                "ACTOR" -> actorDao.deleteActorById(change.entity_id)
                                "MEDIA" -> mediaDao.deleteMediaById(change.entity_id)
                                "TAG" -> tagDao.deleteTagById(change.entity_id)
                            }
                            totalDeleted++
                        }
                        "UPSERT" -> {
                            val data = change.data ?: continue
                            when (change.entity_type.uppercase()) {
                                "MESSAGE" -> {
                                    val remote = parseRemoteMessage(data) ?: continue
                                    applyRemoteMessage(remote, validActorIds)
                                    totalInserted++
                                }
                                "ACTOR" -> {
                                    val actor = parseRemoteActor(data) ?: continue
                                    actorDao.insertActor(actor.toLocalActor())
                                    totalInserted++
                                }
                                "TAG" -> {
                                    val tag = parseRemoteTag(data) ?: continue
                                    tagDao.insertTag(Tag(id = tag.id, name = tag.name, category = tag.category))
                                    totalInserted++
                                }
                                "MEDIA" -> {
                                    // Media 由后端管理，只更新评分/收藏等元数据
                                    val rm = parseRemoteMediaItem(data) ?: continue
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
                                    val inserted = mediaDao.insertMediaIgnore(media)
                                    if (inserted == -1L) mediaDao.updateMedia(media)
                                    totalInserted++
                                }
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "处理变更失败 [${change.operation} ${change.entity_type} #${change.entity_id}]: ${e.message}")
                }
            }

            // 更新 cursor 为 server_time
            cursor = body.server_time

            if (!body.has_more) break
        }

        Log.d(TAG, "增量同步完成：新增/更新 ${totalInserted + totalUpdated}，删除 $totalDeleted")
        SyncResult.Success(totalInserted, totalUpdated, totalDeleted)
    }

    private fun applyRemoteMessage(remote: RemoteMessage, validActorIds: Set<Long>) {
        val createdAtMs = parseIsoToMs(remote.created_at)
        val updatedAtMs = parseIsoToMs(remote.updated_at)
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
        messageDao.deleteMessageMediaByMessageId(remote.id)
        for (rm in remote.media_items) {
            messageDao.insertMessageMedia(MessageMedia(messageId = remote.id, mediaId = rm.id, position = rm.position))
        }
        messageDao.deleteMessageTagsByMessageId(remote.id)
        for (rt in remote.tags) {
            messageDao.insertMessageTag(MessageTag(messageId = remote.id, tagId = rt.id))
        }
    }

    @Suppress("UNCHECKED_CAST")
    private fun parseRemoteMessage(data: Map<String, Any?>): RemoteMessage? = try {
        val mediaRaw = data["media_items"] as? List<Map<String, Any?>> ?: emptyList()
        val tagsRaw = data["tags"] as? List<Map<String, Any?>> ?: emptyList()
        RemoteMessage(
            id = (data["id"] as? Double)?.toLong() ?: return null,
            text = data["text"] as? String,
            actor_id = (data["actor_id"] as? Double)?.toLong(),
            actor_name = data["actor_name"] as? String,
            starred = data["starred"] as? Boolean ?: false,
            created_at = data["created_at"] as? String ?: return null,
            updated_at = data["updated_at"] as? String ?: return null,
            media_items = mediaRaw.mapNotNull { parseRemoteMediaItem(it) },
            tags = tagsRaw.mapNotNull { parseRemoteTagItem(it) },
        )
    } catch (e: Exception) {
        Log.e(TAG, "parseRemoteMessage 失败: ${e.message}")
        null
    }

    @Suppress("UNCHECKED_CAST")
    private fun parseRemoteMediaItem(data: Map<String, Any?>): RemoteMediaItem? = try {
        RemoteMediaItem(
            id = (data["id"] as? Double)?.toLong() ?: return null,
            file_url = data["file_url"] as? String ?: "",
            file_hash = data["file_hash"] as? String,
            file_size = (data["file_size"] as? Double)?.toLong(),
            mime_type = data["mime_type"] as? String,
            width = (data["width"] as? Double)?.toInt(),
            height = (data["height"] as? Double)?.toInt(),
            duration = (data["duration"] as? Double)?.toInt(),
            rating = (data["rating"] as? Double)?.toInt() ?: 0,
            starred = data["starred"] as? Boolean ?: false,
            thumb_url = data["thumb_url"] as? String ?: "",
            position = (data["position"] as? Double)?.toInt() ?: 0,
        )
    } catch (e: Exception) {
        null
    }

    @Suppress("UNCHECKED_CAST")
    private fun parseRemoteActor(data: Map<String, Any?>): RemoteActor? = try {
        RemoteActor(
            id = (data["id"] as? Double)?.toLong() ?: return null,
            name = data["name"] as? String ?: return null,
            description = data["description"] as? String,
            avatar = data["avatar"] as? String,
        )
    } catch (e: Exception) {
        null
    }

    @Suppress("UNCHECKED_CAST")
    private fun parseRemoteTagItem(data: Map<String, Any?>): RemoteTagItem? = try {
        RemoteTagItem(
            id = (data["id"] as? Double)?.toLong() ?: return null,
            name = data["name"] as? String ?: return null,
            category = data["category"] as? String,
        )
    } catch (e: Exception) {
        null
    }

    @Suppress("UNCHECKED_CAST")
    private fun parseRemoteTag(data: Map<String, Any?>): RemoteTagItem? = parseRemoteTagItem(data)

    private fun parseIsoToMs(iso: String): Long = try {
        LocalDateTime.parse(iso).toInstant(ZoneOffset.UTC).toEpochMilli()
    } catch (_: Exception) {
        System.currentTimeMillis()
    }

    companion object {
        private const val TAG = "MessageRepository"
        val TAG_PATTERN = Regex("""#([\w\u4e00-\u9fff\u3400-\u4dbf-]+)""")
    }
}