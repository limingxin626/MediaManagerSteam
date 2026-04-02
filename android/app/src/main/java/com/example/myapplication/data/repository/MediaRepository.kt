package com.example.myapplication.data.repository

import com.example.myapplication.data.database.dao.MediaDao
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.SyncOutboxItem
import kotlinx.coroutines.flow.Flow
import com.google.gson.Gson

/**
 * 媒体数据仓库
 */
class MediaRepository(
    private val mediaDao: MediaDao,
    private val outboxRepository: SyncOutboxRepository? = null
) {
    
    // 查询操作
    fun getAllMedia(): Flow<List<Media>> = mediaDao.getAllMedia()
    
    suspend fun getMediaById(id: Long): Media? = mediaDao.getMediaById(id)

    suspend fun getMediaByIds(ids: List<Long>): List<Media> = mediaDao.getMediaByIds(ids)
    
    fun searchMedia(query: String): Flow<List<Media>> =
        mediaDao.searchMedia(query)
    
    fun getMediaByRatingRange(minRating: Int, maxRating: Int): Flow<List<Media>> =
        mediaDao.getMediaByRatingRange(minRating, maxRating)
    
    fun getHighRatedMedia(): Flow<List<Media>> = mediaDao.getHighRatedMedia()
    
    fun getRecentMedia(limit: Int = 10): Flow<List<Media>> = 
        mediaDao.getRecentMedia(limit)
    
    suspend fun getAllMediaSync(): List<Media> = mediaDao.getAllMediaSync()

    suspend fun getAllMediaIdsSorted(): List<Long> = mediaDao.getAllMediaIdsSorted()

    suspend fun getMediaWindow(offset: Int, limit: Int): List<Media> = mediaDao.getMediaWindow(offset, limit)

    // 统计信息
    suspend fun getMediaCount(): Int = mediaDao.getMediaCount()

    suspend fun getAverageRating(): Float = mediaDao.getAverageRating()
    
    suspend fun getTotalSize(): Long = mediaDao.getTotalSize()
    

    // 写入操作
    suspend fun insertMedia(media: Media): Long {
        // 如果hash已存在，直接返回已有记录的ID，不重复插入
        val existing = mediaDao.getMediaByHash(media.fileHash)
        if (existing != null) {
            return existing.id
        }

        val insertedId = mediaDao.insertMedia(media)

        if (insertedId > 0) {
            val payload = media.copy(id = insertedId)
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_MEDIA,
                entityId = insertedId,
                payloadJson = Gson().toJson(payload)
            )
        }

        return insertedId
    }
    
    suspend fun insertMediaList(mediaList: List<Media>): List<Long> {
        val ids = mediaDao.insertMediaList(mediaList)

        ids.forEachIndexed { index, id ->
            if (id > 0) {
                val payload = mediaList.getOrNull(index)?.copy(id = id) ?: return@forEachIndexed
                outboxRepository?.enqueueUpsert(
                    entityType = SyncOutboxItem.ENTITY_MEDIA,
                    entityId = id,
                    payloadJson = Gson().toJson(payload)
                )
            }
        }

        return ids
    }
    
    suspend fun updateMedia(media: Media) {
        // 更新时间戳
        val updatedMedia = media.copy(updatedAt = System.currentTimeMillis())
        mediaDao.updateMedia(updatedMedia)

        if (updatedMedia.id > 0) {
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_MEDIA,
                entityId = updatedMedia.id,
                payloadJson = Gson().toJson(updatedMedia)
            )
        }
    }
    
    suspend fun deleteMedia(media: Media) {
        // 删除媒体时，关联关系会因为外键约束自动删除
        mediaDao.deleteMedia(media)

        if (media.id > 0) {
            outboxRepository?.enqueueDelete(
                entityType = SyncOutboxItem.ENTITY_MEDIA,
                entityId = media.id
            )
        }
    }
    
    suspend fun deleteMediaById(id: Long) {
        mediaDao.deleteMediaById(id)

        if (id > 0) {
            outboxRepository?.enqueueDelete(
                entityType = SyncOutboxItem.ENTITY_MEDIA,
                entityId = id
            )
        }
    }
    
    suspend fun deleteAllMedia() {
        val allMedia = mediaDao.getAllMediaSync()
        mediaDao.deleteAllMedia()

        for (media in allMedia) {
            if (media.id > 0) {
                outboxRepository?.enqueueDelete(
                    entityType = SyncOutboxItem.ENTITY_MEDIA,
                    entityId = media.id
                )
            }
        }
    }

    // 收藏操作
    suspend fun toggleMediaStarred(mediaId: Long) {
        val media = getMediaById(mediaId) ?: return
        val updated = media.copy(
            starred = !media.starred,
            updatedAt = System.currentTimeMillis()
        )
        mediaDao.updateMedia(updated)
        if (updated.id > 0) {
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_MEDIA,
                entityId = updated.id,
                payloadJson = Gson().toJson(updated)
            )
        }
    }

    // 评分操作
    suspend fun updateMediaRating(mediaId: Long, rating: Int) {
        val media = getMediaById(mediaId)
        media?.let {
            val updatedMedia = it.copy(
                rating = rating.coerceIn(0, 5),
                updatedAt = System.currentTimeMillis()
            )
            mediaDao.updateMedia(updatedMedia)
        }
    }

    companion object {
        private const val TAG = "MediaRepository"
    }
}