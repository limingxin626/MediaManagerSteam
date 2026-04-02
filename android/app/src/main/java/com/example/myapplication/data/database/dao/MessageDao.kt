package com.example.myapplication.data.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import androidx.room.Update
import androidx.paging.PagingSource
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.Message
import com.example.myapplication.data.database.entities.MessageMedia
import com.example.myapplication.data.database.entities.MessageTag
import com.example.myapplication.data.database.entities.MessageWithDetails
import com.example.myapplication.data.database.entities.MessageWithMedia
import com.example.myapplication.data.database.entities.Tag
import kotlinx.coroutines.flow.Flow

/**
 * 消息数据访问接口
 */
@Dao
interface MessageDao {
    // ==================== Message 相关 ====================

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessage(message: Message): Long

    @Update
    suspend fun updateMessage(message: Message)

    @Query("SELECT * FROM messages ORDER BY createdAt DESC")
    fun getAllMessages(): Flow<List<Message>>

    @Query("SELECT * FROM messages ORDER BY createdAt ASC")
    fun getAllMessagesAsc(): Flow<List<Message>>

    @Query("SELECT * FROM messages ORDER BY starred DESC, createdAt DESC")
    fun getAllMessagesStarredFirst(): Flow<List<Message>>

    @Query("SELECT * FROM messages WHERE id = :id")
    suspend fun getMessageById(id: Long): Message?

    @Query("SELECT * FROM messages WHERE actorId = :actorId ORDER BY createdAt DESC")
    fun getMessagesByActorId(actorId: Long): Flow<List<Message>>

    @Query("SELECT * FROM messages WHERE starred = 1 ORDER BY createdAt DESC")
    fun getStarredMessages(): Flow<List<Message>>

    @Query("SELECT * FROM messages WHERE text LIKE '%' || :query || '%' ORDER BY createdAt DESC")
    fun searchMessages(query: String): Flow<List<Message>>

    @Query("DELETE FROM messages WHERE id = :id")
    suspend fun deleteMessage(id: Long)

    // ==================== Relation 查询 ====================

    @Transaction
    @Query("SELECT * FROM messages WHERE id = :id")
    suspend fun getMessageWithDetails(id: Long): MessageWithDetails?

    @Transaction
    @Query("SELECT * FROM messages ORDER BY createdAt DESC")
    fun getAllMessagesWithMedia(): Flow<List<MessageWithMedia>>

    @Transaction
    @Query("SELECT * FROM messages ORDER BY createdAt DESC")
    fun getAllMessagesWithDetails(): Flow<List<MessageWithDetails>>

    // ==================== Paging 查询 ====================

    @Transaction
    @Query("SELECT * FROM messages ORDER BY createdAt DESC")
    fun getMessagesPaged(): PagingSource<Int, MessageWithDetails>

    @Transaction
    @Query("SELECT * FROM messages WHERE text LIKE '%' || :query || '%' ORDER BY createdAt DESC")
    fun searchMessagesPaged(query: String): PagingSource<Int, MessageWithDetails>

    // ==================== Tag-filtered Paging 查询 ====================

    @Transaction
    @Query("""
        SELECT m.* FROM messages m
        INNER JOIN message_tag mt ON m.id = mt.messageId
        WHERE mt.tagId = :tagId
        ORDER BY m.createdAt DESC
    """)
    fun getMessagesByTagPaged(tagId: Long): PagingSource<Int, MessageWithDetails>

    @Transaction
    @Query("""
        SELECT m.* FROM messages m
        INNER JOIN message_tag mt ON m.id = mt.messageId
        WHERE mt.tagId = :tagId AND m.text LIKE '%' || :query || '%'
        ORDER BY m.createdAt DESC
    """)
    fun searchMessagesByTagPaged(tagId: Long, query: String): PagingSource<Int, MessageWithDetails>

    // ==================== Group preview 查询 ====================

    @Transaction
    @Query("""
        SELECT m.* FROM messages m
        INNER JOIN message_tag mt ON m.id = mt.messageId
        WHERE mt.tagId = :tagId
        ORDER BY m.createdAt DESC
        LIMIT 1
    """)
    suspend fun getLastMessageForTag(tagId: Long): MessageWithDetails?

    @Query("SELECT COUNT(*) FROM messages")
    suspend fun getTotalMessageCount(): Int

    @Query("SELECT id FROM messages")
    suspend fun getAllMessageIdsSync(): List<Long>

    @Transaction
    @Query("SELECT * FROM messages ORDER BY createdAt DESC LIMIT 1")
    suspend fun getLastMessage(): MessageWithDetails?

    // ==================== MessageMedia 相关 ====================

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertMessageMedia(messageMedia: MessageMedia): Long

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertMessageMediaList(list: List<MessageMedia>): List<Long>

    @Query("SELECT * FROM message_media WHERE messageId = :messageId ORDER BY position")
    suspend fun getMessageMediaByMessageId(messageId: Long): List<MessageMedia>

    @Query("""
        SELECT m.* FROM media m
        INNER JOIN message_media mm ON m.id = mm.mediaId
        WHERE mm.messageId = :messageId
        ORDER BY mm.position
    """)
    suspend fun getMediaByMessageId(messageId: Long): List<Media>

    @Query("DELETE FROM message_media WHERE messageId = :messageId")
    suspend fun deleteMessageMediaByMessageId(messageId: Long)

    // ==================== MessageTag 相关 ====================

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertMessageTag(messageTag: MessageTag)

    @Query("SELECT tagId FROM message_tag WHERE messageId = :messageId")
    suspend fun getMessageTagIdsByMessageId(messageId: Long): List<Long>

    @Query("""
        SELECT t.* FROM tags t
        INNER JOIN message_tag mt ON t.id = mt.tagId
        WHERE mt.messageId = :messageId
        ORDER BY t.name
    """)
    suspend fun getTagsByMessageId(messageId: Long): List<Tag>

    @Query("""
        SELECT t.* FROM tags t
        INNER JOIN message_tag mt ON t.id = mt.tagId
        WHERE mt.messageId = :messageId
        ORDER BY t.name
    """)
    fun getTagsByMessageIdFlow(messageId: Long): Flow<List<Tag>>

    @Query("DELETE FROM message_tag WHERE messageId = :messageId")
    suspend fun deleteMessageTagsByMessageId(messageId: Long)

    @Query("DELETE FROM message_tag WHERE messageId = :messageId AND tagId = :tagId")
    suspend fun deleteMessageTag(messageId: Long, tagId: Long)
}
