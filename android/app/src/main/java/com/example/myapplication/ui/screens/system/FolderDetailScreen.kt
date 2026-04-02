package com.example.myapplication.ui.screens.system

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.example.myapplication.data.model.SystemMedia
import com.example.myapplication.ui.components.SystemMediaCard
import com.example.myapplication.ui.viewmodel.MediaFilterType
import com.example.myapplication.ui.viewmodel.SystemGalleryViewModel

/**
 * 文件夹详情页面 - 显示单个文件夹内的所有媒体
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FolderDetailScreen(
    folderName: String,
    navController: NavController,
    viewModel: SystemGalleryViewModel,
    modifier: Modifier = Modifier
) {
    val mediaByFolder by viewModel.mediaByFolder.collectAsState()
    val filterType by viewModel.filterType.collectAsState()
    val selectedMedia by viewModel.selectedMedia.collectAsState()
    val isSelectionMode by viewModel.isSelectionMode.collectAsState()
    val uiState by viewModel.uiState.collectAsState()
    
    // 获取当前文件夹的媒体列表
    val currentFolderMedia = mediaByFolder[folderName] ?: emptyList()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = if (isSelectionMode) "已选择 ${selectedMedia.size} 项" else folderName,
                            style = MaterialTheme.typography.titleLarge
                        )
                        if (!isSelectionMode) {
                            Text(
                                text = "${currentFolderMedia.size} 个文件",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
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
                    if (isSelectionMode) {
                        // 选择模式下的操作
                        IconButton(onClick = { viewModel.toggleSelectAll() }) {
                            Icon(
                                imageVector = Icons.Default.MoreVert,
                                contentDescription = if (selectedMedia.size == currentFolderMedia.size) "取消全选" else "全选"
                            )
                        }
                        IconButton(onClick = { viewModel.exitSelectionMode() }) {
                            Icon(
                                imageVector = Icons.Default.MoreVert,
                                contentDescription = "更多"
                            )
                        }
                    } else {
                        // 普通模式下的筛选菜单
                        var showFilterMenu by remember { mutableStateOf(false) }
                        
                        IconButton(onClick = { showFilterMenu = true }) {
                            Icon(
                                imageVector = Icons.Default.MoreVert,
                                contentDescription = "筛选"
                            )
                        }
                        
                        DropdownMenu(
                            expanded = showFilterMenu,
                            onDismissRequest = { showFilterMenu = false }
                        ) {
                            MediaFilterType.values().forEach { type ->
                                DropdownMenuItem(
                                    text = { 
                                        Text(
                                            text = type.displayName,
                                            fontWeight = if (filterType == type) FontWeight.Bold else FontWeight.Normal
                                        ) 
                                    },
                                    onClick = {
                                        viewModel.setFilterType(type)
                                        showFilterMenu = false
                                    }
                                )
                            }
                        }
                    }
                }
            )
        },
        modifier = modifier.fillMaxSize()
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            when {
                uiState.isLoading -> {
                    // 加载中
                    LoadingContent()
                }
                uiState.error != null -> {
                    // 错误状态
                    ErrorContent(
                        error = uiState.error!!,
                        onRetry = { viewModel.loadFolderData() }
                    )
                }
                currentFolderMedia.isEmpty() -> {
                    // 空状态
                    EmptyFolderContent(folderName)
                }
                else -> {
                    // 媒体网格
                    LazyVerticalGrid(
                        columns = GridCells.Adaptive(120.dp),
                        contentPadding = PaddingValues(8.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(
                            items = currentFolderMedia,
                            key = { media -> media.id }
                        ) { media ->
                            SystemMediaCard(
                                media = media,
                                isSelected = selectedMedia.contains(media),
                                isSelectionMode = isSelectionMode,
                                onMediaClick = { clickedMedia ->
                                    if (isSelectionMode) {
                                        viewModel.toggleMediaSelection(clickedMedia)
                                    } else {
                                        // 跳转到系统媒体详情页面
                                        navController.navigate("system_media_detail/${clickedMedia.id}")
                                    }
                                },
                                onMediaLongClick = { longClickedMedia ->
                                    if (!isSelectionMode) {
                                        viewModel.enterSelectionMode()
                                        viewModel.toggleMediaSelection(longClickedMedia)
                                    }
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * 加载中内容
 */
@Composable
private fun LoadingContent() {
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
                text = "正在加载...",
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

/**
 * 错误内容
 */
@Composable
private fun ErrorContent(
    error: String,
    onRetry: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "加载失败",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.error
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = error,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(onClick = onRetry) {
            Text("重试")
        }
    }
}

/**
 * 空文件夹内容
 */
@Composable
private fun EmptyFolderContent(folderName: String) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "文件夹为空",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onSurface
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "「$folderName」文件夹中没有找到媒体文件。",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}