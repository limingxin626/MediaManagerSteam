package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Index

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

    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
) {
    /**
     * 获取实际可用的媒体URI（优先使用本地）
     */
    val filePath: String?
        get() = localMediaPath ?: remoteMediaUrl

    /**
     * 获取实际可用的缩略图路径（优先使用本地）
     */
    val thumbnailPath: String?
        get() = localThumbnailPath ?: remoteThumbnailUrl
}
