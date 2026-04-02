package com.example.myapplication.data.database.dao

import androidx.room.*
import com.example.myapplication.data.database.entities.Tag
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.MediaTag
import com.example.myapplication.data.database.entities.Message
import kotlinx.coroutines.flow.Flow

/**
 * 标签数据访问对象
 */
@Dao
interface TagDao {

    // ===== 标签基础操作 =====

    @Query("SELECT * FROM tags ORDER BY name ASC")
    fun getAllTags(): Flow<List<Tag>>

    @Query("SELECT * FROM tags WHERE id = :tagId")
    suspend fun getTagById(tagId: Long): Tag?

    @Query("SELECT * FROM tags WHERE name = :name")
    suspend fun getTagByName(name: String): Tag?

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertTag(tag: Tag): Long

    @Update
    suspend fun updateTag(tag: Tag)

    @Delete
    suspend fun deleteTag(tag: Tag)

    // ===== 媒体-标签关联操作 =====

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertMediaTag(mediaTag: MediaTag)

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertMediaTags(mediaTags: List<MediaTag>)

    @Delete
    suspend fun deleteMediaTag(mediaTag: MediaTag)

    @Query("DELETE FROM media_tags WHERE mediaId = :mediaId")
    suspend fun deleteAllTagsForMedia(mediaId: Long)

    // ===== 查询操作 =====

    @Query("SELECT t.* FROM tags t INNER JOIN media_tags mt ON t.id = mt.tagId WHERE mt.mediaId = :mediaId ORDER BY t.name")
    fun getTagsForMedia(mediaId: Long): Flow<List<Tag>>

    @Query("SELECT m.* FROM media m INNER JOIN media_tags mt ON m.id = mt.mediaId WHERE mt.tagId = :tagId ORDER BY m.createdAt DESC")
    fun getMediaForTag(tagId: Long): Flow<List<Media>>

    @Query("SELECT COUNT(*) FROM media_tags WHERE tagId = :tagId")
    suspend fun getMediaCountForTag(tagId: Long): Int

    // ===== 消息-标签查询操作 =====

    @Query("SELECT msg.* FROM messages msg INNER JOIN message_tag mt ON msg.id = mt.messageId WHERE mt.tagId = :tagId ORDER BY msg.createdAt DESC")
    fun getMessagesForTag(tagId: Long): Flow<List<Message>>

    @Query("SELECT COUNT(*) FROM message_tag WHERE tagId = :tagId")
    suspend fun getMessageCountForTag(tagId: Long): Int

    @Query("SELECT * FROM tags WHERE name LIKE '%' || :query || '%' ORDER BY name ASC")
    fun searchTags(query: String): Flow<List<Tag>>
}
