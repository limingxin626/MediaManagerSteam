package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * 媒体来源枚举
 */
enum class MediaSource(val displayName: String) {
    LOCAL("本地"),      // 来自手机本地相册
    REMOTE("远程");     // 来自远程服务器
    
    companion object {
        fun fromDisplayName(displayName: String): MediaSource? {
            return entries.find { it.displayName == displayName }
        }
    }
}

/**
 * 媒体类型枚举
 */
enum class MediaType(val displayName: String) {
    VIDEO("视频"),
    IMAGE("图片"),
    PREVIEW("预览");

    companion object {
        /**
         * 根据显示名称获取枚举值
         */
        fun fromDisplayName(displayName: String): MediaType? {
            return values().find { it.displayName == displayName }
        }
        
        /**
         * 获取所有显示名称列表
         */
        fun getDisplayNames(): List<String> {
            return values().map { it.displayName }
        }
    }
}

/**
 * 媒体排序方式枚举
 */
enum class MediaSortOrder(val displayName: String) {
    TITLE_ASC("标题升序"),
    TITLE_DESC("标题降序"),
    RATING_ASC("评分升序"),
    RATING_DESC("评分降序"),
    DURATION_ASC("时长升序"),
    DURATION_DESC("时长降序"),
    SIZE_ASC("大小升序"),
    SIZE_DESC("大小降序"),
    CREATED_ASC("添加时间升序"),
    CREATED_DESC("添加时间降序");
    
    companion object {
        /**
         * 根据显示名称获取枚举值
         */
        fun fromDisplayName(displayName: String): MediaSortOrder? {
            return entries.find { it.displayName == displayName }
        }
    }
}

/**
 * 媒体实体类
 * 支持本地媒体（MediaStore中的媒体文件）和远程媒体（来自服务器）
 */
@Entity(tableName = "media")
data class Media(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    val name: String,                      // 名称
    val description: String = "",           // 描述
    val type: MediaType,                   // 媒体类型：VIDEO 或 IMAGE
    val source: MediaSource = MediaSource.LOCAL, // 媒体来源：LOCAL 或 REMOTE
    
    // ==================== 远程媒体字段 ====================
    val remoteMediaUrl: String? = null,    // 远程媒体文件URL
    val remoteThumbnailUrl: String? = null, // 远程缩略图URL
    
    // ==================== 本地媒体字段 ====================
    val localMediaPath: String? = null,    // 本地媒体文件路径
    val localThumbnailPath: String? = null, // 本地缩略图路径
    val isDownloaded: Boolean = false,     // 是否已下载到本地
    val downloadedAt: Long? = null,        // 下载时间
    
    // ==================== 媒体属性字段 ====================
    val duration: Long? = null,            // 视频时长（秒），图片为null
    val fileSize: Long = 0,                // 文件大小（字节）
    val width: Int = 0,                    // 宽度（像素）
    val height: Int = 0,                   // 高度（像素）
    
    // ==================== 应用管理字段 ====================
    val rating: Int = 0,                   // 评分 (0-5)
    val actorId: Long? = null,             // 所属演员ID（null表示未分配）
    val groupId: Long? = null,             // 所属组合ID（null表示未分配）
    val parentId: Long? = null,            // 父媒体ID（用于预览图等）
    
    val date: String? = null,              // 日期 (YYYY-MM-DD格式)
    val fileHash: String? = null,          // 文件哈希值
    val viewCount: Int = 0,                // 观看次数
    val lastViewedAt: Long? = null,        // 最后观看时间戳
    val startTime: Float? = null,          // 开始时间（秒）
    val timestamp: Float? = null,          // 当前播放位置（秒）
    val endTime: Float? = null,            // 结束时间（秒）
    
    val createdAt: Long = System.currentTimeMillis(), // 创建时间
    val updatedAt: Long = System.currentTimeMillis()  // 更新时间
) {
    
    /**
     * 是否是本地媒体
     */
    val isLocal: Boolean
        get() = source == MediaSource.LOCAL
    
    /**
     * 是否是远程媒体
     */
    val isRemote: Boolean
        get() = source == MediaSource.REMOTE
    
    /**
     * 是否可以本地播放/显示（本地媒体或已下载的远程媒体）
     */
    val isLocallyAvailable: Boolean
        get() = isLocal || isDownloaded
    
    /**
     * 宽高比 (width/height)，用于瀑布流布局
     */
    val aspectRatio: Float?
        get() = if (height > 0) width.toFloat() / height.toFloat() else null
    
    /**
     * 分辨率字符串 (例如: "1920x1080")
     */
    val resolution: String?
        get() = if (width > 0 && height > 0) "${width}x${height}" else null
    
    /**
     * 获取实际可用的媒体URI（优先使用本地）
     */
    val effectiveUri: String?
        get() = when {
            localMediaPath != null -> localMediaPath
            else -> remoteMediaUrl
        }
    
    /**
     * 获取实际可用的缩略图路径（优先使用本地）
     */
    val effectiveThumbnailPath: String?
        get() = when {
            localThumbnailPath != null -> localThumbnailPath
            remoteThumbnailUrl != null -> remoteThumbnailUrl
            else -> null
        }
    
    /**
     * 获取系统媒体URI用于显示（兼容旧代码）
     */
    val displayUri: String
        get() = effectiveUri ?: ""
    
    /**
     * 获取显示用的文件名
     */
    val displayFileName: String
        get() = name
    
    /**
     * 获取用于显示的URI
     */
    fun getDisplayUri(): android.net.Uri? {
        return effectiveUri?.let { android.net.Uri.parse(it) }
    }
    
    /**
     * 获取格式化的文件大小
     */
    fun getFormattedSize(): String {
        return when {
            fileSize < 1024 -> "${fileSize}B"
            fileSize < 1024 * 1024 -> "${fileSize / 1024}KB"
            fileSize < 1024 * 1024 * 1024 -> "${fileSize / (1024 * 1024)}MB"
            else -> "${fileSize / (1024 * 1024 * 1024)}GB"
        }
    }
    
    /**
     * 获取格式化的时长（仅视频）
     */
    fun getFormattedDuration(): String? {
        return duration?.let { durationSeconds ->
            val minutes = durationSeconds / 60
            val hours = minutes / 60
            
            when {
                hours > 0 -> String.format("%d:%02d:%02d", hours, minutes % 60, durationSeconds % 60)
                minutes > 0 -> String.format("%d:%02d", minutes, durationSeconds % 60)
                else -> String.format("0:%02d", durationSeconds)
            }
        }
    }
    
    companion object {
        /**
         * 建议下载的最大文件大小（默认50MB）
         */
        const val RECOMMENDED_DOWNLOAD_SIZE_THRESHOLD = 50L * 1024 * 1024
        
        /**
         * 判断是否建议下载到本地
         */
        fun shouldDownload(size: Long, threshold: Long = RECOMMENDED_DOWNLOAD_SIZE_THRESHOLD): Boolean {
            return size <= threshold
        }
    }
}