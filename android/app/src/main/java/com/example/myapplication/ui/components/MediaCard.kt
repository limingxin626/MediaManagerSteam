package com.example.myapplication.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.ui.theme.InstagramGradientEnd
import com.example.myapplication.ui.theme.InstagramGradientMiddle
import com.example.myapplication.ui.theme.InstagramGradientStart
import com.example.myapplication.ui.theme.TextSecondary

/**
 * Instagram/Pinterest 风格媒体卡片组件
 * 适用于瀑布流布局，支持动态高度
 */
@Composable
fun MediaCard(
    media: Media,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    useAspectRatio: Boolean = false,
    baseWidth: Float = 200f,
    thumbnailOnly: Boolean = false
) {
    // 缓存所有计算结果
    val durationText = remember(media.durationMs) {
        media.durationMs?.let { ms ->
            val totalSeconds = ms / 1000
            "${totalSeconds / 60}:${String.format("%02d", totalSeconds % 60)}"
        }
    }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .aspectRatio(1f),
        onClick = onClick,
        shape = RoundedCornerShape(4.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 0.dp,
        shadowElevation = 0.dp
    ) {
        Column(
            modifier = Modifier.fillMaxWidth()
        ) {
            // 封面区域
            Box(
                contentAlignment = Alignment.Center
            ) {
                // 缩略图加载
                val displayUri = media.filePath ?: ""
                val thumbnailUri = media.thumbnailPath?: displayUri

                OptimizedThumbnail(
                    thumbnailPath = thumbnailUri,
                    modifier = Modifier.fillMaxSize()
                )

                // 底部渐变遮罩（用于显示时长等信息）
                val isVideo = media.mimeType?.startsWith("video/") == true
                if (isVideo && durationText != null) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(40.dp)
                            .align(Alignment.BottomCenter)
                            .background(
                                Brush.verticalGradient(
                                    colors = listOf(
                                        Color.Transparent, Color.Black.copy(alpha = 0.6f)
                                    )
                                )
                            )
                    )
                }

                // 视频播放图标 - 居中半透明
                if (isVideo) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.Center)
                            .size(36.dp)
                            .background(
                                Color.Black.copy(alpha = 0.4f), RoundedCornerShape(18.dp)
                            ), contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.PlayArrow,
                            contentDescription = "播放",
                            modifier = Modifier.size(20.dp),
                            tint = Color.White
                        )
                    }
                }

                // 视频时长 - 右下角
                if (isVideo && durationText != null) {
                    Text(
                        text = durationText,
                        modifier = Modifier
                            .align(Alignment.BottomEnd)
                            .padding(8.dp),
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontSize = 11.sp, fontWeight = FontWeight.Medium
                        ),
                        color = Color.White
                    )
                }

                // 收藏标记 - 右上角
                if (media.starred) {
                    Icon(
                        imageVector = Icons.Default.Star,
                        contentDescription = "已收藏",
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(6.dp)
                            .size(16.dp),
                        tint = Color(0xFFFFD700)
                    )
                }

                // 评分标签 - 左上角（如果有评分）
                if (media.rating > 0) {
                    Surface(
                        modifier = Modifier
                            .align(Alignment.TopStart)
                            .padding(6.dp),
                        shape = RoundedCornerShape(4.dp),
                        color = InstagramGradientStart.copy(alpha = 0.9f)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(2.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Star,
                                contentDescription = null,
                                modifier = Modifier.size(10.dp),
                                tint = Color.White
                            )
                            Text(
                                text = "${media.rating}",
                                style = MaterialTheme.typography.labelSmall.copy(
                                    fontSize = 10.sp, fontWeight = FontWeight.SemiBold
                                ),
                                color = Color.White
                            )
                        }
                    }
                }
            }
        }
    }
}

