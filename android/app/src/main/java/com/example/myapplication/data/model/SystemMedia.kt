package com.example.myapplication.data.model

import android.net.Uri

/**
 * 系统媒体文件数据模型
 */
data class SystemMedia(
    val id: Long,                    // MediaStore中的ID
    val uri: Uri,                    // 文件URI
    val displayName: String,         // 显示名称
    val relativePath: String?,       // 相对路径
    val mimeType: String,           // MIME类型
    val size: Long,                 // 文件大小（字节）
    val dateAdded: Long,            // 添加时间（时间戳）
    val dateModified: Long,         // 修改时间（时间戳）
    val width: Int = 0,             // 宽度（像素）
    val height: Int = 0,            // 高度（像素）
    val duration: Long? = null,     // 视频时长（毫秒，仅视频）
    val bucketDisplayName: String?, // 文件夹名称
    val bucketId: String?           // 文件夹ID
) {
    /**
     * 是否为图片
     */
    val isImage: Boolean
        get() = mimeType.startsWith("image/")

    /**
     * 是否为视频
     */
    val isVideo: Boolean
        get() = mimeType.startsWith("video/")

    /**
     * 获取分辨率字符串
     */
    val resolution: String?
        get() = if (width > 0 && height > 0) "${width}x${height}" else null

    /**
     * 获取宽高比
     */
    val aspectRatio: Float?
        get() = if (width > 0 && height > 0) width.toFloat() / height.toFloat() else null

    /**
     * 获取格式化的文件大小
     */
    fun getFormattedSize(): String {
        return when {
            size < 1024 -> "${size}B"
            size < 1024 * 1024 -> "${size / 1024}KB"
            size < 1024 * 1024 * 1024 -> "${size / (1024 * 1024)}MB"
            else -> "${size / (1024 * 1024 * 1024)}GB"
        }
    }

    /**
     * 获取格式化的时长（仅视频）
     */
    fun getFormattedDuration(): String? {
        return duration?.let { durationMs ->
            val seconds = durationMs / 1000
            val minutes = seconds / 60
            val hours = minutes / 60

            when {
                hours > 0 -> String.format("%d:%02d:%02d", hours, minutes % 60, seconds % 60)
                minutes > 0 -> String.format("%d:%02d", minutes, seconds % 60)
                else -> String.format("0:%02d", seconds)
            }
        }
    }

}