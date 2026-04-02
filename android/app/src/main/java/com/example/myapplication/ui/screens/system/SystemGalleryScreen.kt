package com.example.myapplication.ui.screens.system

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.input.nestedscroll.nestedScroll
import com.example.myapplication.LocalBottomBarVisible
import androidx.core.content.ContextCompat
import com.example.myapplication.ui.components.SystemMediaCard
import com.example.myapplication.ui.viewmodel.MediaFilterType
import com.example.myapplication.ui.viewmodel.SystemGalleryViewModel

/**
 * 系统相册页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SystemGalleryScreen(
    navController: androidx.navigation.NavController,
    viewModel: SystemGalleryViewModel,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    
    val uiState by viewModel.uiState.collectAsState()
    val mediaList by viewModel.mediaList.collectAsState()
    val filterType by viewModel.filterType.collectAsState()
    val hasPermission by viewModel.hasPermission.collectAsState()
    
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
            ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
        }
        
        if (allGranted) {
            viewModel.setPermissionGranted(true)
        } else {
            permissionLauncher.launch(permissions)
        }
    }
    
    // 底部导航栏控制
    val bottomBarVisible = LocalBottomBarVisible.current
    val nestedScrollConnection = remember {
        object : NestedScrollConnection {
            override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset {
                if (available.y < -5f) {
                    bottomBarVisible.value = false
                } else if (available.y > 5f) {
                    bottomBarVisible.value = true
                }
                return Offset.Zero
            }
        }
    }

    Column(
        modifier = modifier.fillMaxSize().nestedScroll(nestedScrollConnection)
    ) {
        // 顶部栏
        TopAppBar(
            title = {
                Text(
                    text = "系统相册",
                    style = MaterialTheme.typography.titleLarge
                )
            },
            actions = {
                // 筛选菜单
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
                            text = { Text(type.displayName) },
                            onClick = {
                                viewModel.setFilterType(type)
                                showFilterMenu = false
                            }
                        )
                    }
                }
            }
        )
        
        // 主内容区域
        Box(
            modifier = Modifier.fillMaxSize()
        ) {
            when {
                !hasPermission -> {
                    // 没有权限
                    PermissionRequiredContent(
                        onRequestPermission = {
                            val permissions = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                                arrayOf(
                                    Manifest.permission.READ_MEDIA_IMAGES,
                                    Manifest.permission.READ_MEDIA_VIDEO
                                )
                            } else {
                                arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE)
                            }
                            permissionLauncher.launch(permissions)
                        }
                    )
                }
                uiState.isLoading -> {
                    // 加载中
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
                }
                uiState.error != null -> {
                    // 错误状态
                    ErrorContent(
                        error = uiState.error!!,
                        onRetry = { viewModel.refresh() }
                    )
                }
                mediaList.isEmpty() -> {
                    // 空状态
                    EmptyContent()
                }
                else -> {
                    // 网格视图
                    LazyVerticalGrid(
                        columns = GridCells.Fixed(3),
                        contentPadding = PaddingValues(top = 2.dp, start = 2.dp, end = 2.dp, bottom = 88.dp),
                        horizontalArrangement = Arrangement.spacedBy(2.dp),
                        verticalArrangement = Arrangement.spacedBy(2.dp)
                    ) {
                        items(
                            items = mediaList,
                            key = { it.id }
                        ) { media ->
                            SystemMediaCard(
                                media = media,
                                isSelected = false,
                                isSelectionMode = false,
                                onMediaClick = { clickedMedia ->
                                    // 跳转到系统媒体详情页面
                                    navController.navigate("system_media_detail/${clickedMedia.id}")
                                },
                                onMediaLongClick = { }
                            )
                        }
                    }
                }
            }
        }
    }

}

/**
 * 权限请求内容
 */
@Composable
private fun PermissionRequiredContent(
    onRequestPermission: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "需要存储权限",
            style = MaterialTheme.typography.headlineSmall
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Button(onClick = onRequestPermission) {
            Text("授予权限")
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
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "加载失败",
            style = MaterialTheme.typography.headlineSmall
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Button(onClick = onRetry) {
            Text("重试")
        }
    }
}

/**
 * 空内容
 */
@Composable
private fun EmptyContent() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "没有找到媒体文件",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}