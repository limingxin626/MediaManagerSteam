package com.example.myapplication.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.example.myapplication.data.database.entities.Media

/**
 * Instagram 风格的简化版媒体缩略图卡片
 * 正方形布局，紧凑设计，适用于网格展示
 */
@Composable
fun MediaThumbnailCard(
    media: Media,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .aspectRatio(1f)
            .clickable(onClick = onClick)
    ) {
        // 简化实现，使用 Media 实体中的 filePath
        val displayPath = media.filePath ?: ""

        // 使用 OptimizedThumbnail 处理所有媒体类型
        OptimizedThumbnail(
            thumbnailPath = displayPath,
            modifier = Modifier.fillMaxSize()
        )

        // 视频标识（右上角小图标）
        if (media.mimeType?.startsWith("video/") == true) {
            Icon(
                Icons.Default.PlayArrow,
                contentDescription = "视频",
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(4.dp)
                    .size(20.dp),
                tint = Color.White
            )
        }
    }
}

/**
 * 媒体缩略图网格行
 * 每行显示指定数量的媒体缩略图
 */
@Composable
fun MediaThumbnailRow(
    mediaList: List<Media>,
    startIndex: Int,
    columnsPerRow: Int = 3,
    onMediaClick: (Media, List<Media>) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        for (col in 0 until columnsPerRow) {
            val index = startIndex + col
            if (index < mediaList.size) {
                val media = mediaList[index]

                MediaThumbnailCard(
                    media = media,
                    onClick = { onMediaClick(media, mediaList) },
                    modifier = Modifier.weight(1f)
                )
            } else {
                // 空白占位
                Spacer(modifier = Modifier.weight(1f))
            }
        }
    }
}
