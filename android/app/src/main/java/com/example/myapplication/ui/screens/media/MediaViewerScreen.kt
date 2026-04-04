package com.example.myapplication.ui.screens.media

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import coil.compose.AsyncImage
import coil.request.ImageRequest
import androidx.compose.ui.platform.LocalContext
import com.example.myapplication.LocalBottomBarVisible
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.ui.components.OptimizedThumbnail
import com.example.myapplication.ui.components.TelegramVideoPlayer
import kotlinx.coroutines.launch

/**
 * 全屏媒体查看器 — Telegram 风格
 * 支持图片（Coil）和视频（ExoPlayer），左右滑动切换
 * 底部显示当前 message 的横向缩略图导航条
 *
 * 两种模式:
 * 1. 列表模式 (mediaIdList 非空): 用于 message 内的小数量媒体，直接加载全部
 * 2. 浏览模式 (mediaIdList 为空): 用于 media 页面的大量媒体，窗口化分页加载
 */
private const val WINDOW_SIZE = 20 // 每次加载的窗口大小
private const val PRELOAD_THRESHOLD = 5 // 距离边界多少时触发预加载

@Composable
fun MediaViewerScreen(
    initialMediaId: Long,
    messageId: Long,
    mediaIdList: List<Long>,
    databaseManager: DatabaseManager,
    navController: NavController
) {
    val bottomBarVisible = LocalBottomBarVisible.current
    val coroutineScope = rememberCoroutineScope()

    // 隐藏底部导航栏
    DisposableEffect(Unit) {
        bottomBarVisible.value = false
        onDispose { bottomBarVisible.value = true }
    }

    if (mediaIdList.isNotEmpty()) {
        // 模式1: 列表模式 — 来自 message，少量媒体，直接全部加载
        ListModeViewer(
            initialMediaId = initialMediaId,
            mediaIdList = mediaIdList,
            databaseManager = databaseManager,
            navController = navController
        )
    } else {
        // 模式2: 浏览模式 — 来自 media 页面，窗口化加载
        BrowseModeViewer(
            initialMediaId = initialMediaId,
            databaseManager = databaseManager,
            navController = navController
        )
    }
}

/**
 * 列表模式：直接加载所有 ID 对应的媒体（适用于 message 内少量媒体）
 */
@Composable
private fun ListModeViewer(
    initialMediaId: Long,
    mediaIdList: List<Long>,
    databaseManager: DatabaseManager,
    navController: NavController
) {
    val coroutineScope = rememberCoroutineScope()
    val mediaList = remember { mutableStateListOf<Media>() }

    LaunchedEffect(mediaIdList) {
        val loaded = databaseManager.mediaRepository.getMediaByIds(mediaIdList)
            .sortedBy { mediaIdList.indexOf(it.id) }
        mediaList.clear()
        mediaList.addAll(loaded)
    }

    if (mediaList.isEmpty()) {
        LoadingBox()
        return
    }

    val startIndex = mediaList.indexOfFirst { it.id == initialMediaId }.coerceAtLeast(0)
    val pagerState = rememberPagerState(initialPage = startIndex) { mediaList.size }
    val stripListState = rememberLazyListState()

    LaunchedEffect(pagerState.currentPage) {
        val viewportWidth = stripListState.layoutInfo.viewportSize.width
        val itemWidthPx = stripListState.layoutInfo.visibleItemsInfo.firstOrNull()?.size ?: viewportWidth
        val offset = -(viewportWidth / 2 - itemWidthPx / 2)
        stripListState.scrollToItem(
            index = pagerState.currentPage,
            scrollOffset = offset
        )
    }

    MediaViewerContent(
        mediaList = mediaList,
        pagerState = pagerState,
        stripListState = stripListState,
        totalCount = mediaList.size,
        currentGlobalIndex = pagerState.currentPage,
        databaseManager = databaseManager,
        navController = navController,
        coroutineScope = coroutineScope
    )
}

/**
 * 浏览模式：窗口化分页加载（适用于 media 页面的大量媒体）
 * 只加载当前位置附近的媒体窗口，滑动到边界时自动扩展
 */
@Composable
private fun BrowseModeViewer(
    initialMediaId: Long,
    databaseManager: DatabaseManager,
    navController: NavController
) {
    val coroutineScope = rememberCoroutineScope()

    // 全局状态
    var totalCount by remember { mutableIntStateOf(0) }
    var globalIndex by remember { mutableIntStateOf(0) } // initialMediaId 在全局排序中的位置
    val mediaList = remember { mutableStateListOf<Media>() }
    var windowStart by remember { mutableIntStateOf(0) } // 当前窗口在全局列表中的起始偏移
    var isInitialized by remember { mutableStateOf(false) }
    var isExpanding by remember { mutableStateOf(false) }

    // 初始化：获取所有 ID 列表，定位当前媒体，加载初始窗口
    LaunchedEffect(initialMediaId) {
        val allIds = databaseManager.mediaRepository.getAllMediaIdsSorted()
        totalCount = allIds.size
        if (totalCount == 0) {
            isInitialized = true
            return@LaunchedEffect
        }

        // 找到 initialMediaId 在排序列表中的位置
        val idx = allIds.indexOf(initialMediaId).coerceAtLeast(0)
        globalIndex = idx

        // 计算窗口起始位置（尽量让目标在窗口中间）
        val halfWindow = WINDOW_SIZE / 2
        val start = (idx - halfWindow).coerceAtLeast(0)
        val end = (start + WINDOW_SIZE).coerceAtMost(totalCount)
        val actualStart = (end - WINDOW_SIZE).coerceAtLeast(0)

        windowStart = actualStart
        val loaded = databaseManager.mediaRepository.getMediaWindow(actualStart, end - actualStart)
        mediaList.clear()
        mediaList.addAll(loaded)
        isInitialized = true
    }

    if (!isInitialized || mediaList.isEmpty()) {
        LoadingBox()
        return
    }

    // pager 中的本地索引 = 全局索引 - windowStart
    val localStartIndex = (globalIndex - windowStart).coerceIn(0, mediaList.size - 1)
    val pagerState = rememberPagerState(initialPage = localStartIndex) { mediaList.size }
    val stripListState = rememberLazyListState()

    // 当前页面在全局列表中的索引
    val currentGlobalIdx = windowStart + pagerState.currentPage

    LaunchedEffect(pagerState.currentPage) {
        val viewportWidth = stripListState.layoutInfo.viewportSize.width
        val itemWidthPx = stripListState.layoutInfo.visibleItemsInfo.firstOrNull()?.size ?: viewportWidth
        val offset = -(viewportWidth / 2 - itemWidthPx / 2)
        stripListState.scrollToItem(
            index = pagerState.currentPage,
            scrollOffset = offset
        )
    }

    // 边界预加载：接近窗口边缘时扩展
    LaunchedEffect(pagerState.currentPage) {
        if (isExpanding) return@LaunchedEffect

        val localIdx = pagerState.currentPage
        val distToEnd = mediaList.size - 1 - localIdx
        val distToStart = localIdx

        // 向后扩展（用户往右/往下滑）
        if (distToEnd < PRELOAD_THRESHOLD && windowStart + mediaList.size < totalCount) {
            isExpanding = true
            val currentEnd = windowStart + mediaList.size
            val loadCount = WINDOW_SIZE.coerceAtMost(totalCount - currentEnd)
            if (loadCount > 0) {
                val moreMedia = databaseManager.mediaRepository.getMediaWindow(currentEnd, loadCount)
                mediaList.addAll(moreMedia)
            }
            isExpanding = false
        }

        // 向前扩展（用户往左/往上滑）
        if (distToStart < PRELOAD_THRESHOLD && windowStart > 0) {
            isExpanding = true
            val loadCount = WINDOW_SIZE.coerceAtMost(windowStart)
            val newStart = windowStart - loadCount
            val moreMedia = databaseManager.mediaRepository.getMediaWindow(newStart, loadCount)
            // 在列表头部插入
            mediaList.addAll(0, moreMedia)
            windowStart = newStart
            // pagerState 的 currentPage 需要偏移，因为我们在头部插入了数据
            // HorizontalPager 基于 index, 新增的数据在前面会自动把 currentPage 向后推
            // 但 mutableStateList 变化后 pager 会重组，需要手动跳转维持位置
            pagerState.scrollToPage(pagerState.currentPage + loadCount)
            isExpanding = false
        }
    }

    MediaViewerContent(
        mediaList = mediaList,
        pagerState = pagerState,
        stripListState = stripListState,
        totalCount = totalCount,
        currentGlobalIndex = currentGlobalIdx,
        databaseManager = databaseManager,
        navController = navController,
        coroutineScope = coroutineScope
    )
}

@Composable
private fun LoadingBox() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
        contentAlignment = Alignment.Center
    ) {
        CircularProgressIndicator(color = Color.White)
    }
}

/**
 * 共享的查看器内容（pager + 顶部栏 + 底部缩略图）
 */
@Composable
private fun MediaViewerContent(
    mediaList: List<Media>,
    pagerState: androidx.compose.foundation.pager.PagerState,
    stripListState: androidx.compose.foundation.lazy.LazyListState,
    totalCount: Int,
    currentGlobalIndex: Int,
    databaseManager: DatabaseManager,
    navController: NavController,
    coroutineScope: kotlinx.coroutines.CoroutineScope
) {
    // 用于收藏状态变更的可变列表引用
    val mutableMediaList = mediaList as? MutableList<Media>

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .systemBarsPadding()
    ) {
        HorizontalPager(
            state = pagerState,
            modifier = Modifier.fillMaxSize(),
            beyondViewportPageCount = 0 // 只保留当前页的 ExoPlayer，避免 OOM
        ) { page ->
            val media = mediaList[page]
            val isVideo = media.mimeType?.startsWith("video/") == true
            val isCurrentPage = pagerState.settledPage == page
            if (isVideo) {
                val path = media.filePath
                if (path != null) {
                    TelegramVideoPlayer(
                        videoPath = path,
                        autoPlay = isCurrentPage,
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(bottom = if (mediaList.size > 1) 76.dp else 0.dp)
                    )
                } else {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text("无法加载视频", color = Color.White)
                    }
                }
            } else {
                val imagePath = media.filePath ?: media.thumbnailPath
                AsyncImage(
                    model = ImageRequest.Builder(LocalContext.current)
                        .data(imagePath)
                        .crossfade(true)
                        .build(),
                    contentDescription = null,
                    contentScale = ContentScale.Fit,
                    modifier = Modifier.fillMaxSize()
                )
            }
        }

        // 顶部：关闭按钮 + 页码
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.TopCenter)
                .padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = { navController.popBackStack() }) {
                Icon(
                    imageVector = Icons.Default.Close,
                    contentDescription = "关闭",
                    tint = Color.White,
                    modifier = Modifier.size(28.dp)
                )
            }
            Spacer(modifier = Modifier.weight(1f))

            // 收藏按钮
            if (mediaList.isNotEmpty()) {
                val currentMedia = mediaList[pagerState.currentPage]
                IconButton(onClick = {
                    coroutineScope.launch {
                        databaseManager.mediaRepository.toggleMediaStarred(currentMedia.id)
                        val idx = pagerState.currentPage
                        mutableMediaList?.let {
                            it[idx] = it[idx].copy(starred = !it[idx].starred)
                        }
                    }
                }) {
                    Icon(
                        imageVector = if (currentMedia.starred) Icons.Filled.Star else Icons.Outlined.Star,
                        contentDescription = if (currentMedia.starred) "取消收藏" else "收藏",
                        tint = if (currentMedia.starred) Color(0xFFFFD700) else Color.White
                    )
                }
            }

            if (totalCount > 1) {
                Text(
                    text = "${currentGlobalIndex + 1} / $totalCount",
                    color = Color.White,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.padding(end = 16.dp)
                )
            }
        }

        // 底部：横向缩略图导航条（多于1个媒体时显示）
        if (mediaList.size > 1) {
            MediaStripBar(
                mediaList = mediaList,
                currentIndex = pagerState.currentPage,
                listState = stripListState,
                pagerState = pagerState,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
            )
        }
    }
}

@Composable
private fun MediaStripBar(
    mediaList: List<Media>,
    currentIndex: Int,
    listState: androidx.compose.foundation.lazy.LazyListState,
    pagerState: androidx.compose.foundation.pager.PagerState,
    modifier: Modifier = Modifier
) {
    val coroutineScope = rememberCoroutineScope()

    Box(
        modifier = modifier
            .background(Color.Black.copy(alpha = 0.55f))
            .padding(vertical = 8.dp)
    ) {
        LazyRow(
            state = listState,
            contentPadding = PaddingValues(horizontal = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(4.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            itemsIndexed(mediaList) { index, media ->
                val isSelected = index == currentIndex
                val thumbPath = media.thumbnailPath ?: media.filePath
                val isVideo = media.mimeType?.startsWith("video/") == true

                Box(
                    modifier = Modifier
                        .size(60.dp)
                        .then(
                            if (isSelected) Modifier.border(2.dp, Color.White, RoundedCornerShape(4.dp))
                            else Modifier
                        )
                        .clip(RoundedCornerShape(4.dp))
                        .clickable {
                            coroutineScope.launch {
                                pagerState.animateScrollToPage(index)
                            }
                        }
                ) {
                    OptimizedThumbnail(
                        thumbnailPath = thumbPath,
                        modifier = Modifier.fillMaxSize()
                    )
                    // 视频标记
                    if (isVideo) {
                        Box(
                            modifier = Modifier
                                .size(16.dp)
                                .align(Alignment.BottomEnd)
                                .padding(2.dp)
                                .background(Color.Black.copy(alpha = 0.6f), RoundedCornerShape(2.dp)),
                            contentAlignment = Alignment.Center
                        ) {
                            androidx.compose.foundation.Canvas(modifier = Modifier.size(8.dp)) {
                                // 小三角形播放标记
                                val path = androidx.compose.ui.graphics.Path().apply {
                                    moveTo(0f, 0f)
                                    lineTo(size.width, size.height / 2f)
                                    lineTo(0f, size.height)
                                    close()
                                }
                                drawPath(path, color = Color.White)
                            }
                        }
                    }
                    // 未选中时轻微遮罩
                    if (!isSelected) {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(Color.Black.copy(alpha = 0.35f))
                        )
                    }
                }
            }
        }
    }
}
