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
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
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
import androidx.navigation.NavController
import com.example.myapplication.navigation.Routes
import com.example.myapplication.ui.components.FolderCard
import com.example.myapplication.ui.viewmodel.MediaFilterType
import com.example.myapplication.ui.viewmodel.SystemGalleryViewModel

/**
 * 系统相册文件夹视图页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SystemFolderViewScreen(
    navController: NavController,
    viewModel: SystemGalleryViewModel,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    val mediaByFolder by viewModel.mediaByFolder.collectAsState()
    val filterType by viewModel.filterType.collectAsState()
    val expandedFolders by viewModel.expandedFolders.collectAsState()
    val selectedMedia by viewModel.selectedMedia.collectAsState()
    val isSelectionMode by viewModel.isSelectionMode.collectAsState()
    val hasPermission by viewModel.hasPermission.collectAsState()
    val context = androidx.compose.ui.platform.LocalContext.current
    
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
    
    // 检查权限并加载数据
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
            androidx.core.content.ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
        }
        
        if (allGranted) {
            viewModel.setPermissionGranted(true)
        } else {
            permissionLauncher.launch(permissions)
        }
    }
    
    // 自动加载文件夹数据
    LaunchedEffect(hasPermission) {
        if (hasPermission) {
            viewModel.loadFolderData()
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

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = if (isSelectionMode) "已选择 ${selectedMedia.size} 项" else "文件夹视图",
                            style = MaterialTheme.typography.titleLarge
                        )
                        if (!isSelectionMode && hasPermission) {
                            Text(
                                text = "${mediaByFolder.size} 个文件夹",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                },
                actions = {
                    if (isSelectionMode) {
                        // 选择模式下的操作
                        IconButton(onClick = { viewModel.toggleSelectAll() }) {
                            Icon(
                                imageVector = Icons.Default.MoreVert,
                                contentDescription = if (selectedMedia.size == mediaByFolder.values.flatten().size) "取消全选" else "全选"
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
        modifier = modifier.fillMaxSize().nestedScroll(nestedScrollConnection)
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            when {
                !hasPermission -> {
                    // 没有权限
                    NoPermissionContent(
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
                    LoadingContent()
                }
                uiState.error != null -> {
                    // 错误状态
                    ErrorContent(
                        error = uiState.error!!,
                        onRetry = { viewModel.loadFolderData() }
                    )
                }
                mediaByFolder.isEmpty() -> {
                    // 空状态
                    EmptyFolderContent()
                }
                else -> {
                    // 文件夹网格
                    LazyVerticalGrid(
                        columns = GridCells.Adaptive(160.dp),
                        contentPadding = PaddingValues(top = 16.dp, start = 16.dp, end = 16.dp, bottom = 88.dp),
                        horizontalArrangement = Arrangement.spacedBy(16.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        items(
                            items = mediaByFolder.toList(),
                            key = { (folder, _) -> folder }
                        ) { (folder, mediaInFolder) ->
                            FolderCard(
                                folderName = folder,
                                mediaList = mediaInFolder,
                                onFolderClick = { clickedFolder ->
                                    // 跳转到文件夹详情页面
                                    navController.navigate(Routes.folderDetail(clickedFolder))
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
 * 无权限内容
 */
@Composable
private fun NoPermissionContent(
    onRequestPermission: () -> Unit
) {
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
            text = "请授予存储访问权限以查看文件夹内容。",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        Button(onClick = onRequestPermission) {
            Text("授予权限")
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
                text = "正在加载文件夹...",
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
private fun EmptyFolderContent() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "没有找到文件夹",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onSurface
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "设备中没有包含媒体文件的文件夹。",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}