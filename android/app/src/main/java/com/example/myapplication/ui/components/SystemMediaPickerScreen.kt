package com.example.myapplication.ui.components

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.navigation.NavController
import com.example.myapplication.data.model.SystemMedia
import com.example.myapplication.ui.viewmodel.MediaFilterType
import com.example.myapplication.ui.viewmodel.SystemGalleryViewModel

/**
 * 系统媒体选择器页面
 * 用于从系统媒体中选择媒体添加到组合，不进行复制
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SystemMediaPickerScreen(
    navController: NavController,
    viewModel: SystemGalleryViewModel,
    onMediaSelected: (List<SystemMedia>) -> Unit,
    allowMultiple: Boolean = true,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState()
    val mediaList by viewModel.mediaList.collectAsState()
    val filterType by viewModel.filterType.collectAsState()
    val hasPermission by viewModel.hasPermission.collectAsState()

    // 选择状态管理
    var selectedMedia by remember { mutableStateOf(setOf<SystemMedia>()) }

    // 权限请求
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val granted = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions[Manifest.permission.READ_MEDIA_IMAGES] == true &&
                    permissions[Manifest.permission.READ_MEDIA_VIDEO] == true
        } else {
            permissions[Manifest.permission.READ_EXTERNAL_STORAGE] == true
        }
        viewModel.setPermissionGranted(granted)
    }

    // 检查权限
    LaunchedEffect(Unit) {
        val permissions = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            arrayOf(
                Manifest.permission.READ_MEDIA_IMAGES,
                Manifest.permission.READ_MEDIA_VIDEO
            )
        } else {
            arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE)
        }

        val allGranted = permissions.all { permission ->
            ContextCompat.checkSelfPermission(
                context,
                permission
            ) == PackageManager.PERMISSION_GRANTED
        }

        if (allGranted) {
            viewModel.setPermissionGranted(true)
        } else {
            permissionLauncher.launch(permissions)
        }
    }

    // 加载数据
    LaunchedEffect(hasPermission) {
        if (hasPermission && mediaList.isEmpty()) {
            viewModel.loadSystemMedia()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = if (selectedMedia.isNotEmpty())
                                "已选择 ${selectedMedia.size} 项"
                            else "选择系统媒体",
                            style = MaterialTheme.typography.titleLarge
                        )
                        if (mediaList.isNotEmpty()) {
                            Text(
                                text = "${mediaList.size} 个文件",
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
                    if (selectedMedia.isNotEmpty()) {
                        TextButton(
                            onClick = {
                                onMediaSelected(selectedMedia.toList())
                                navController.popBackStack()
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Default.Check,
                                contentDescription = "确认",
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("确认")
                        }
                    }

                    // 筛选菜单
                    var showFilterMenu by remember { mutableStateOf(false) }

                    TextButton(onClick = { showFilterMenu = true }) {
                        Text(filterType.displayName)
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
                !hasPermission -> {
                    // 没有权限
                    NoPermissionContent()
                }

                uiState.isLoading -> {
                    // 加载中
                    LoadingContent()
                }

                uiState.error != null -> {
                    // 错误状态
                    ErrorContent(
                        error = uiState.error!!,
                        onRetry = { viewModel.loadSystemMedia() }
                    )
                }

                mediaList.isEmpty() -> {
                    // 空状态
                    EmptyContent()
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
                            items = mediaList,
                            key = { media -> media.id }
                        ) { media ->
                            SystemMediaCard(
                                media = media,
                                isSelected = selectedMedia.contains(media),
                                isSelectionMode = true,
                                onMediaClick = { clickedMedia ->
                                    if (allowMultiple) {
                                        selectedMedia = if (selectedMedia.contains(clickedMedia)) {
                                            selectedMedia - clickedMedia
                                        } else {
                                            selectedMedia + clickedMedia
                                        }
                                    } else {
                                        // 单选模式
                                        onMediaSelected(listOf(clickedMedia))
                                        navController.popBackStack()
                                    }
                                },
                                onMediaLongClick = { /* 不需要长按功能 */ }
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * 无权限内容
 */
@Composable
private fun NoPermissionContent() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "需要存储权限",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onSurface
        )

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = "需要存储访问权限才能选择系统媒体。",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
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
                text = "正在加载媒体...",
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
 * 空状态内容
 */
@Composable
private fun EmptyContent() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "没有找到媒体",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onSurface
        )

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = "设备中没有找到可选择的媒体文件。",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}