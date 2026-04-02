package com.example.myapplication.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import coil.compose.SubcomposeAsyncImage
import coil.request.ImageRequest
import coil.request.CachePolicy
import java.io.File
import android.net.Uri
import coil.compose.AsyncImage

import android.os.Build
import android.util.Size
import androidx.compose.ui.graphics.asImageBitmap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * 优化的媒体缩略图组件
 * 针对滚动性能进行了特殊优化，减少卡顿
 */
@Composable
fun OptimizedThumbnail(
    thumbnailPath: String?,
    modifier: Modifier = Modifier
) {
    // 获取Context在Composable作用域中
    val context = LocalContext.current
    
    // 简化实现，使用默认颜色和图标
    val typeColor = Color(0xFF388E3C) // 绿色
    val typeIcon = Icons.Default.Star
    
    if (!thumbnailPath.isNullOrEmpty()) {
        // 判断路径类型
        val isSystemUri = thumbnailPath.startsWith("content://")
        val isNetworkUrl = thumbnailPath.startsWith("http://") || thumbnailPath.startsWith("https://")
        
        // 检查文件/URI可用性
        val mediaExists = remember(thumbnailPath) {
            when {
                isSystemUri -> true // 对于系统URI，假设存在（由系统保证）
                isNetworkUrl -> true // 对于网络URL，假设存在（由网络请求处理）
                else -> File(thumbnailPath).exists() // 对于文件路径，检查文件是否存在
            }
        }
        
        if (mediaExists) {
            // 高性能图片加载配置
            val imageRequest = remember(thumbnailPath) {
                val dataSource = when {
                    isSystemUri -> android.net.Uri.parse(thumbnailPath) // 系统URI直接解析
                    isNetworkUrl -> thumbnailPath // 网络URL直接使用字符串
                    else -> File(thumbnailPath) // 文件路径
                }
                
                ImageRequest.Builder(context)
                    .data(dataSource)
                    .size(coil.size.Size.ORIGINAL) // 使用原始分辨率，避免二次缩放模糊
                    .crossfade(false) // 禁用交叉淡入，减少GPU负担
                    .allowHardware(true) // 启用硬件解码
                    .memoryCachePolicy(CachePolicy.ENABLED)
                    .diskCachePolicy(CachePolicy.ENABLED)
                    .networkCachePolicy(if (isNetworkUrl) CachePolicy.ENABLED else CachePolicy.DISABLED)
                    .build()
            }
            
            SubcomposeAsyncImage(
                model = imageRequest,
                contentDescription = "媒体缩略图",
                contentScale = ContentScale.Crop,
                modifier = modifier,
                error = {
                    // 如果加载失败，显示默认图标
                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = typeColor.copy(alpha = 0.1f),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Icon(
                            imageVector = typeIcon,
                            contentDescription = "",
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(24.dp),
                            tint = typeColor
                        )
                    }
                }
            )
        } else {
            // 文件不存在时显示默认图标
            Surface(
                modifier = modifier,
                color = typeColor.copy(alpha = 0.1f),
                shape = RoundedCornerShape(8.dp)
            ) {
                Icon(
                    imageVector = typeIcon,
                    contentDescription = "",
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    tint = typeColor
                )
            }
        }
    } else {
        // 缓存默认图标的修饰符
        val iconModifier = remember {
            Modifier
                .fillMaxSize()
                .padding(24.dp)
        }
        
        // 默认图标 - 使用缓存的颜色和图标
        Surface(
            modifier = modifier,
            color = typeColor.copy(alpha = 0.1f),
            shape = RoundedCornerShape(8.dp)
        ) {
            Icon(
                imageVector = typeIcon,
                contentDescription = "",
                modifier = iconModifier,
                tint = typeColor
            )
        }
    }
}



/**
 * 大尺寸媒体缩略图组件
 * 用于详情页和编辑页面
 */
@Composable
fun LargeMediaThumbnail(
    thumbnailPath: String?,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        OptimizedThumbnail(
            thumbnailPath = thumbnailPath,
            modifier = Modifier.fillMaxSize()
        )
    }
}

/**
 * 演员头像组件
 * 使用 Coil 进行高效图片加载和缓存
 */
@Composable
fun OptimizedAvatar(
    avatarPath: String?,
    actorName: String,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    
    if (!avatarPath.isNullOrEmpty()) {
        // 判断是系统URI还是文件路径
        val isSystemUri = avatarPath.startsWith("content://")
        
        // 检查资源可用性
        val avatarExists = remember(avatarPath) {
            if (isSystemUri) {
                true // 系统URI假设存在
            } else {
                File(avatarPath).exists()
            }
        }
        
        if (avatarExists) {
            val imageRequest = remember(avatarPath) {
                val dataSource = if (isSystemUri) {
                    Uri.parse(avatarPath)
                } else {
                    File(avatarPath)
                }
                
                ImageRequest.Builder(context)
                    .data(dataSource)
                    .crossfade(true)
                    .size(240, 240) // 固定尺寸提高缓存效率
                    .build()
            }
            
            SubcomposeAsyncImage(
                model = imageRequest,
                contentDescription = "${actorName}的头像",
                contentScale = ContentScale.Crop,
                modifier = modifier.fillMaxSize(),
                error = {
                    // 加载失败时显示默认头像
                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = MaterialTheme.colorScheme.surfaceVariant
                    ) {
                        Icon(
                            Icons.Default.Person,
                            contentDescription = "默认头像",
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(24.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            )
        } else {
            // 文件不存在时显示默认头像
            Surface(
                modifier = modifier.fillMaxSize(),
                color = MaterialTheme.colorScheme.surfaceVariant
            ) {
                Icon(
                    Icons.Default.Person,
                    contentDescription = "默认头像",
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    } else {
        // 路径为空时显示默认头像
        Surface(
            modifier = modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.surfaceVariant
        ) {
            Icon(
                Icons.Default.Person,
                contentDescription = "默认头像",
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

