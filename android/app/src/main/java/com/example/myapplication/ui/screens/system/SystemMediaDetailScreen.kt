package com.example.myapplication.ui.screens.system

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.example.myapplication.ui.viewmodel.SystemGalleryViewModel

/**
 * 系统媒体详情页面 - 全屏显示
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SystemMediaDetailScreen(
    mediaId: Long,
    navController: NavController,
    viewModel: SystemGalleryViewModel,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current

    val mediaList by viewModel.mediaList.collectAsState()
    val mediaByFolder by viewModel.mediaByFolder.collectAsState()
    val uiState by viewModel.uiState.collectAsState()
    val hasPermission by viewModel.hasPermission.collectAsState()

    // 确保权限和数据加载
    LaunchedEffect(Unit) {
        if (!hasPermission) {
            viewModel.setPermissionGranted(true)
        }
    }

    // 查找指定的媒体
    val currentMedia = remember(mediaId, mediaList, mediaByFolder) {
        // 首先在网格列表中查找
        mediaList.find { it.id == mediaId } ?:
        // 如果没找到，在文件夹分组中查找
        mediaByFolder.values.flatten().find { it.id == mediaId }
    }

    // 如果正在加载，显示加载状态
    if (uiState.isLoading) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                CircularProgressIndicator()
                Text(
                    text = "正在加载媒体文件...",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        }
        return
    }

    if (currentMedia == null) {
        // 媒体未找到的错误状态
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    text = "媒体文件未找到",
                    style = MaterialTheme.typography.headlineSmall
                )
                Text(
                    text = "媒体ID: $mediaId",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = "网格列表: ${mediaList.size} 项",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = "文件夹数量: ${mediaByFolder.size}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Button(
                    onClick = { navController.popBackStack() }
                ) {
                    Text("返回")
                }
            }
        }
        return
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = currentMedia.displayName,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "返回"
                        )
                    }
                },
                actions = {
                    // 编辑按钮
                    IconButton(
                        onClick = {
                            navController.navigate("system_media_edit/$mediaId")
                        }
                    ) {
                        Icon(
                            imageVector = Icons.Default.Edit,
                            contentDescription = "编辑"
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // 媒体显示区域
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .background(Color.Black),
                contentAlignment = Alignment.Center
            ) {
                if (currentMedia.isVideo) {
                    // 视频播放器占位符（可以后续添加实际的视频播放器）
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        AsyncImage(
                            model = ImageRequest.Builder(context)
                                .data(currentMedia.uri)
                                .size(800, 800)
                                .crossfade(true)
                                .build(),
                            contentDescription = currentMedia.displayName,
                            modifier = Modifier.fillMaxSize(),
                            contentScale = ContentScale.Fit
                        )

                        // 播放按钮覆盖层
                        Box(
                            modifier = Modifier
                                .size(80.dp)
                                .background(
                                    Color.Black.copy(alpha = 0.6f),
                                    RoundedCornerShape(40.dp)
                                )
                                .clickable {
                                    // TODO: 实现视频播放
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.PlayArrow,
                                contentDescription = "播放视频",
                                tint = Color.White,
                                modifier = Modifier.size(40.dp)
                            )
                        }
                    }
                } else {
                    // 图片显示
                    AsyncImage(
                        model = ImageRequest.Builder(context)
                            .data(currentMedia.uri)
                            .crossfade(true)
                            .build(),
                        contentDescription = currentMedia.displayName,
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Fit
                    )
                }
            }

            // 媒体信息区域
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // 文件名
                    Text(
                        text = currentMedia.displayName,
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )

                    // 基本信息行
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        // 媒体类型
                        Surface(
                            color = MaterialTheme.colorScheme.primaryContainer,
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text(
                                text = if (currentMedia.isVideo) "视频" else "图片",
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        }

                        // 文件大小
                        Text(
                            text = currentMedia.getFormattedSize(),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    // 分辨率
                    currentMedia.resolution?.let { resolution ->
                        InfoRow(label = "分辨率", value = resolution)
                    }

                    // 视频时长
                    if (currentMedia.isVideo) {
                        currentMedia.getFormattedDuration()?.let { duration ->
                            InfoRow(label = "时长", value = duration)
                        }
                    }

                    // 文件夹
                    currentMedia.bucketDisplayName?.let { bucket ->
                        InfoRow(label = "文件夹", value = bucket)
                    }

                    // 文件路径
                    currentMedia.relativePath?.let { path ->
                        InfoRow(
                            label = "路径",
                            value = path,
                            maxLines = 2
                        )
                    }
                }
            }
        }
    }
}

/**
 * 信息行组件
 */
@Composable
private fun InfoRow(
    label: String,
    value: String,
    maxLines: Int = 1,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top
    ) {
        Text(
            text = "$label:",
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.widthIn(max = 80.dp)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.weight(1f),
            maxLines = maxLines,
            overflow = TextOverflow.Ellipsis
        )
    }
}