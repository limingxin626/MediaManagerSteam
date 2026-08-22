package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 媒体实体类
 * 对应后端的Media模型
 */
@Entity(
    tableName = "media",
    indices = [
        Index(value = ["fileHash"], unique = true)
    ]
)
data class Media(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    // ==================== 远程媒体字段 ====================
    val remoteMediaUrl: String? = null,
    val remoteThumbnailUrl: String? = null,

    // ==================== 本地媒体字段 ====================
    val sourceType: String = SOURCE_REMOTE,
    val contentUri: String? = null,
    val originalFileName: String? = null,
    val localMediaPath: String? = null,
    val localThumbnailPath: String? = null,
    val isDownloaded: Boolean = false,
    val downloadedAt: Long? = null,

    val fileHash: String,
    val fileSize: Long? = null,
    val mimeType: String? = null,
    val width: Int? = null,
    val height: Int? = null,
    val durationMs: Long? = null,
    val rating: Int = 0,
    val starred: Boolean = false,
    val viewCount: Int = 0,
    val lastViewedAt: Long? = null,

    // ==================== 视频预览（章节）字段 ====================
    val videoMediaId: Long? = null,
    val frameMs: Int? = null,
    val startMs: Int? = null,
    val endMs: Int? = null,

    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
) {
    /**
     * 获取实际可用的媒体URI（优先使用本地）
     */
    val filePath: String?
        get() = primaryMediaPath()

    /**
     * 获取实际可用的缩略图路径（优先使用本地）
     */
    val thumbnailPath: String?
        get() = primaryThumbnailPath()

    fun primaryMediaPath(contentUriAvailable: Boolean = true): String? = when {
        localMediaPath != null -> localMediaPath
        contentUriAvailable && contentUri != null -> contentUri
        else -> remoteMediaUrl
    }

    fun primaryThumbnailPath(contentUriAvailable: Boolean = true): String? = when {
        localThumbnailPath != null -> localThumbnailPath
        contentUriAvailable && contentUri != null -> contentUri
        remoteThumbnailUrl != null -> remoteThumbnailUrl
        else -> remoteMediaUrl
    }

    companion object {
        const val SOURCE_REMOTE = "REMOTE"
        const val SOURCE_APP_FILE = "APP_FILE"
        const val SOURCE_MEDIA_STORE = "MEDIA_STORE"
    }
}
