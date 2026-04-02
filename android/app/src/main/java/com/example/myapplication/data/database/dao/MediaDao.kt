package com.example.myapplication.data.database.dao

import androidx.room.*
import com.example.myapplication.data.database.entities.Media
import kotlinx.coroutines.flow.Flow

/**
 * 媒体数据访问对象
 */
@Dao
interface MediaDao {
    
    // 查询所有媒体
    @Query("SELECT * FROM media ORDER BY createdAt DESC")
    fun getAllMedia(): Flow<List<Media>>
    
    // 根据ID查询媒体
    @Query("SELECT * FROM media WHERE id = :id")
    suspend fun getMediaById(id: Long): Media?

    // 根据ID列表批量查询媒体
    @Query("SELECT * FROM media WHERE id IN (:ids)")
    suspend fun getMediaByIds(ids: List<Long>): List<Media>
    

    

    

    
    // 搜索媒体（按本地路径和远程URL）
    @Query("""
        SELECT * FROM media 
        WHERE localMediaPath LIKE '%' || :query || '%'
           OR remoteMediaUrl LIKE '%' || :query || '%'
        ORDER BY createdAt DESC
    """)
    fun searchMedia(query: String): Flow<List<Media>>
    
    // 根据评分范围筛选媒体
    @Query("SELECT * FROM media WHERE rating BETWEEN :minRating AND :maxRating ORDER BY rating DESC")
    fun getMediaByRatingRange(minRating: Int, maxRating: Int): Flow<List<Media>>

    // 获取高评分媒体
    @Query("SELECT * FROM media WHERE rating >= 4 ORDER BY rating DESC")
    fun getHighRatedMedia(): Flow<List<Media>>

    // 获取收藏媒体
    @Query("SELECT * FROM media WHERE starred = 1 ORDER BY createdAt DESC")
    fun getStarredMedia(): Flow<List<Media>>

    // 根据文件哈希查询媒体
    @Query("SELECT * FROM media WHERE fileHash = :hash")
    suspend fun getMediaByHash(hash: String): Media?
    
    // 获取最近添加的媒体
    @Query("SELECT * FROM media ORDER BY createdAt DESC LIMIT :limit")
    fun getRecentMedia(limit: Int = 10): Flow<List<Media>>
    
    // 获取媒体统计信息
    @Query("SELECT COUNT(*) FROM media")
    suspend fun getMediaCount(): Int
    

    
    @Query("SELECT AVG(rating) FROM media")
    suspend fun getAverageRating(): Float
    
    @Query("SELECT SUM(fileSize) FROM media")
    suspend fun getTotalSize(): Long
    
    // 插入媒体
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMedia(media: Media): Long

    // 插入媒体（已存在则跳过，不触发 CASCADE 删除）
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertMediaIgnore(media: Media): Long
    
    // 插入多个媒体
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMediaList(mediaList: List<Media>): List<Long>
    
    // 更新媒体
    @Update
    suspend fun updateMedia(media: Media)
    
    // 删除媒体
    @Delete
    suspend fun deleteMedia(media: Media)
    
    // 根据ID删除媒体
    @Query("DELETE FROM media WHERE id = :id")
    suspend fun deleteMediaById(id: Long)
    
    // 删除所有媒体
    @Query("DELETE FROM media")
    suspend fun deleteAllMedia()
    
    // 获取所有媒体ID（按创建时间降序），用于全屏浏览时的分页索引
    @Query("SELECT id FROM media ORDER BY createdAt DESC")
    suspend fun getAllMediaIdsSorted(): List<Long>

    // 根据偏移量和数量获取媒体窗口（用于全屏浏览器分页加载）
    @Query("SELECT * FROM media ORDER BY createdAt DESC LIMIT :limit OFFSET :offset")
    suspend fun getMediaWindow(offset: Int, limit: Int): List<Media>

    // 同步获取所有媒体（用于批量更新）
    @Query("SELECT * FROM media ORDER BY createdAt DESC")
    suspend fun getAllMediaSync(): List<Media>
    
    // 批量更新媒体
    @Update
    suspend fun updateMediaList(mediaList: List<Media>)
    

    
    // 更新媒体的下载状态
    @Query("UPDATE media SET isDownloaded = :isDownloaded, localMediaPath = :localMediaPath, localThumbnailPath = :localThumbnailPath, downloadedAt = :downloadedAt, updatedAt = :updatedAt WHERE id = :mediaId")
    suspend fun updateDownloadStatus(
        mediaId: Long,
        isDownloaded: Boolean,
        localMediaPath: String?,
        localThumbnailPath: String?,
        downloadedAt: Long?,
        updatedAt: Long = System.currentTimeMillis()
    )
}