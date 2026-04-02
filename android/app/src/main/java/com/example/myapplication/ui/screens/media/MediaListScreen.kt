package com.example.myapplication.ui.screens.media

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.items as gridItems
import androidx.compose.foundation.lazy.grid.rememberLazyGridState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.zIndex
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import com.example.myapplication.LocalBottomBarVisible
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.ui.components.*
import com.example.myapplication.ui.theme.InstagramGradientMiddle
import com.example.myapplication.ui.viewmodel.MediaViewModel

/**
 * Instagram/Pinterest 风格媒体列表页面 - 两列瀑布流
 */
@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun MediaListScreen(
    viewModel: MediaViewModel,
    databaseManager: DatabaseManager,
    onMediaClick: (Media, List<Media>) -> Unit = { _, _ -> },
    modifier: Modifier = Modifier
) {
    // 优化状态收集
    val uiState by viewModel.uiState.collectAsState()
    val mediaList by viewModel.mediaList.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    
    // 局部搜索输入状态
    var localSearchQuery by remember { mutableStateOf("") }
    
    LaunchedEffect(searchQuery) {
        localSearchQuery = searchQuery
    }
    
    // 底部筛选面板状态
    var showFilterSheet by remember { mutableStateOf(false) }
    


    val isListEmpty by remember {
        derivedStateOf<Boolean> { mediaList.isEmpty() }
    }

    val hasFilters by remember {
        derivedStateOf<Boolean> { searchQuery.isNotBlank() }
    }

    val gridState = rememberLazyGridState()

    val snackbarHostState = remember { SnackbarHostState() }

    // 顶部栏高度状态
    var topBarHeightPx by remember { mutableFloatStateOf(0f) }
    val topBarHeightDp = with(LocalDensity.current) { topBarHeightPx.toDp() }

    // 底部导航栏控制
    val bottomBarVisible = LocalBottomBarVisible.current
    val nestedScrollConnection = remember {
        object : NestedScrollConnection {
            override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset {
                // 底部栏逻辑
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
        snackbarHost = { SnackbarHost(snackbarHostState) },
        modifier = modifier.fillMaxSize().nestedScroll(nestedScrollConnection),
        containerColor = MaterialTheme.colorScheme.surface
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(bottom = paddingValues.calculateBottomPadding())
        ) {
            // 内容区域 (Layer 1)
            Box(
                modifier = Modifier
                    .fillMaxSize()
            ) {
                when {
                    uiState.isLoading -> {
                        LoadingIndicator()
                    }

                    isListEmpty -> {
                        Box(modifier = Modifier.padding(top = topBarHeightDp)) {
                            EmptyState(
                                message = if (hasFilters) {
                                    "没有找到符合条件的媒体"
                                } else {
                                    "暂无媒体数据\n点击下方按钮添加媒体"
                                }
                            )
                        }
                    }

                    else -> {
                        // 固定3列网格，1:1比例
                        LazyVerticalGrid(
                            columns = GridCells.Fixed(3),
                            state = gridState,
                            contentPadding = PaddingValues(top = topBarHeightDp + 4.dp, start = 2.dp, end = 2.dp, bottom = 88.dp),
                            horizontalArrangement = Arrangement.spacedBy(2.dp),
                            verticalArrangement = Arrangement.spacedBy(2.dp)
                        ) {
                            gridItems(
                                items = mediaList,
                                key = { it.id }
                            ) { media ->
                                val onClickCallback =
                                    remember(media.id, mediaList) { { onMediaClick(media, mediaList) } }

                                MediaCard(
                                    media = media,
                                    onClick = onClickCallback,
                                    useAspectRatio = true,
                                    thumbnailOnly = true
                                )
                            }

                            // 底部间距
                            item {
                                Spacer(modifier = Modifier.height(100.dp))
                            }
                        }
                    }
                }

            }

            // Instagram 风格搜索和筛选栏 (Layer 2 - Header)
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .onGloballyPositioned { coordinates ->
                        topBarHeightPx = coordinates.size.height.toFloat()
                    }
                    .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.98f))
                    .statusBarsPadding()
                    .zIndex(1f)
            ) {
                // Instagram 风格搜索和筛选栏
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 12.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    SearchBar(
                        query = localSearchQuery,
                        onQueryChanged = { localSearchQuery = it },
                        onSearch = { viewModel.searchMedia(it) },
                        placeholder = "搜索媒体...",
                        modifier = Modifier.weight(1f)
                    )
                
                    InstagramFilterButton(
                        hasActiveFilters = false,
                        onClick = { showFilterSheet = true }
                    )
                }
            

            }
        }
    }

    // 错误消息处理
    uiState.error?.let { error ->
        LaunchedEffect(error) {
            viewModel.clearError()
        }
    }

    // 成功消息处理
    uiState.message?.let { message ->
        LaunchedEffect(message) {
            viewModel.clearMessage()
        }
    }
    

}

/**
 * 媒体激活筛选标签
 */
@Composable
private fun MediaActiveFilterChip(
    label: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(14.dp),
        color = InstagramGradientMiddle.copy(alpha = 0.1f)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Text(
                text = label,
                fontSize = 12.sp,
                color = InstagramGradientMiddle,
                fontWeight = FontWeight.Medium
            )
            Icon(
                imageVector = Icons.Outlined.Close,
                contentDescription = "移除",
                modifier = Modifier.size(14.dp),
                tint = InstagramGradientMiddle
            )
        }
    }
}