package com.example.myapplication.ui.components

import android.os.Build
import android.util.Size
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.example.myapplication.data.model.SystemMedia
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * 系统缩略图加载组件
 */
@Composable
private fun SystemThumbnailImage(
    media: SystemMedia,
    modifier: Modifier = Modifier,
    contentScale: ContentScale = ContentScale.Crop
) {
    val context = LocalContext.current
    // 使用媒体ID作为缓存键，避免重复加载
    var thumbnailBitmap by remember(media.id) { mutableStateOf<android.graphics.Bitmap?>(null) }
    var isLoading by remember(media.id) { mutableStateOf(true) }

    LaunchedEffect(media.id) {
        withContext(Dispatchers.IO) {
            try {
                val bitmap = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    // Android 10+ 使用系统缩略图API
                    context.contentResolver.loadThumbnail(
                        media.uri,
                        Size(300, 300),
                        null
                    )
                } else {
                    // Android 9及以下使用传统方式
                    null
                }
                thumbnailBitmap = bitmap
            } catch (e: Exception) {
                thumbnailBitmap = null
            } finally {
                isLoading = false
            }
        }
    }

    when {
        isLoading -> {
            // 加载中显示占位符
            Box(
                modifier = modifier,
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(modifier = Modifier.size(24.dp))
            }
        }

        thumbnailBitmap != null -> {
            // 显示系统缩略图
            androidx.compose.foundation.Image(
                bitmap = thumbnailBitmap!!.asImageBitmap(),
                contentDescription = media.displayName,
                modifier = modifier,
                contentScale = contentScale
            )
        }

        else -> {
            // Fallback到Coil加载原图
            AsyncImage(
                model = ImageRequest.Builder(context)
                    .data(media.uri)
                    .size(300, 300)
                    .crossfade(200) // 减少交叉淡入时间
                    .memoryCacheKey(media.id.toString()) // 使用媒体ID作为缓存键
                    .diskCacheKey(media.id.toString()) // 磁盘缓存键
                    .build(),
                contentDescription = media.displayName,
                modifier = modifier,
                contentScale = contentScale
            )
        }
    }
}

/**
 * 系统媒体卡片组件
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SystemMediaCard(
    media: SystemMedia,
    isSelected: Boolean = false,
    isSelectionMode: Boolean = false,
    onMediaClick: (SystemMedia) -> Unit,
    onMediaLongClick: (SystemMedia) -> Unit = {},
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current

    Card(
        modifier = modifier
            .fillMaxWidth()
            .aspectRatio(1f)
            .clickable {
                onMediaClick(media)
            },
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        shape = RoundedCornerShape(0.dp) // 使用直角，不要圆角
    ) {
        Box(
            modifier = Modifier.fillMaxSize()
        ) {
            // 媒体缩略图 - 使用系统原生缩略图
            SystemThumbnailImage(
                media = media,
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )

            // 视频播放图标
            if (media.isVideo) {
                Box(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .size(32.dp)
                        .background(
                            Color.Black.copy(alpha = 0.5f),
                            RoundedCornerShape(16.dp)
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.PlayArrow,
                        contentDescription = "视频",
                        tint = Color.White,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }

            // 视频时长显示
            if (media.isVideo && media.duration != null) {
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(4.dp)
                        .background(
                            Color.Black.copy(alpha = 0.7f),
                            RoundedCornerShape(4.dp)
                        )
                        .padding(horizontal = 4.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = media.getFormattedDuration() ?: "",
                        color = Color.White,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            // 选择模式下的选中状态
            if (isSelectionMode) {
                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(4.dp)
                ) {
                    if (isSelected) {
                        Icon(
                            imageVector = Icons.Default.CheckCircle,
                            contentDescription = "已选中",
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(24.dp)
                        )
                    } else {
                        Box(
                            modifier = Modifier
                                .size(24.dp)
                                .background(
                                    Color.White.copy(alpha = 0.7f),
                                    RoundedCornerShape(12.dp)
                                )
                                .padding(2.dp)
                                .background(
                                    Color.Transparent,
                                    RoundedCornerShape(10.dp)
                                )
                        )
                    }
                }
            }

            // 选中状态的遮罩
            if (isSelected) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            MaterialTheme.colorScheme.primary.copy(alpha = 0.3f)
                        )
                )
            }
        }
    }
}

/**
 * 媒体信息卡片（用于详情显示）
 */
@Composable
fun SystemMediaInfoCard(
    media: SystemMedia,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // 文件名
            Text(
                text = media.displayName,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )

            // 基本信息
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = if (media.isVideo) "视频" else "图片",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = media.getFormattedSize(),
                    style = MaterialTheme.typography.bodyMedium
                )
            }

            // 分辨率
            media.resolution?.let { resolution ->
                Text(
                    text = "分辨率: $resolution",
                    style = MaterialTheme.typography.bodyMedium
                )
            }

            // 视频时长
            if (media.isVideo) {
                media.getFormattedDuration()?.let { duration ->
                    Text(
                        text = "时长: $duration",
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
            }

            // 文件夹
            media.bucketDisplayName?.let { bucket ->
                Text(
                    text = "文件夹: $bucket",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        }
    }
}