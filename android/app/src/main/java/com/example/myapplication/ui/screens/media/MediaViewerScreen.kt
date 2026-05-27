package com.example.myapplication.ui.screens.media

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.systemBarsPadding
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
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.example.myapplication.LocalBottomBarVisible
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.repository.MessageRepository
import com.example.myapplication.ui.components.OptimizedThumbnail
import com.example.myapplication.ui.components.TelegramVideoPlayer
import com.example.myapplication.ui.components.ZoomableImage
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
    navController: NavController,
    filterTagId: Long? = null,
    filterActorId: Long? = null,
    filterQuery: String = ""
) {
    val bottomBarVisible = LocalBottomBarVisible.current
    val coroutineScope = rememberCoroutineScope()

    // 隐藏底部导航栏
    DisposableEffect(Unit) {
        bottomBarVisible.value = false
        onDispose { bottomBarVisible.value = true }
    }

    if (mediaIdList.isNotEmpty()) {
        // 有媒体ID列表（来自media页面筛选或message页面联动）
        if (messageId > 0) {
            // 模式1: 列表模式（联动）— 来自 message，可跨 group 滑动
            FederatedListModeViewer(
                initialMediaId = initialMediaId,
                initialMessageId = messageId,
                initialMediaIdList = mediaIdList,
                filter = MessageRepository.MediaViewerFilter(
                    tagId = filterTagId,
                    actorId = filterActorId,
                    searchQuery = filterQuery
                ),
                databaseManager = databaseManager,
                navController = navController
            )
        } else {
            // 模式2: 浏览模式 — 来自 media 页面，使用传入的筛选后列表
            BrowseModeViewer(
                initialMediaId = initialMediaId,
                initialMediaIdList = mediaIdList,
                databaseManager = databaseManager,
                navController = navController
            )
        }
    } else {
        // 无媒体ID列表，从头加载（fallback）
        BrowseModeViewer(
            initialMediaId = initialMediaId,
            databaseManager = databaseManager,
            navController = navController
        )
    }
}

/**
 * 列表模式（联动）：以入口 message 为锚点，pager 数据 = 当前过滤集合下、按 createdAt DESC + 组内 position 拉平的 media 序列。
 * 滑到边缘时按需加载相邻 message 的 media（append/prepend）。
 */
@Composable
private fun FederatedListModeViewer(
    initialMediaId: Long,
    initialMessageId: Long,
    initialMediaIdList: List<Long>,
    filter: MessageRepository.MediaViewerFilter,
    databaseManager: DatabaseManager,
    navController: NavController
) {
    val coroutineScope = rememberCoroutineScope()
    val mediaList = remember { mutableStateListOf<Media>() }
    // 每个 page 对应所属 messageId，用于切片缩略图条
    val mediaMessageIds = remember { mutableStateListOf<Long>() }
    var isInitialized by remember { mutableStateOf(false) }
    var isExpanding by remember { mutableStateOf(false) }
    var headMessageId by remember { mutableStateOf(initialMessageId) } // 已加载序列中最新（视觉左侧）
    var tailMessageId by remember { mutableStateOf(initialMessageId) } // 已加载序列中最旧（视觉右侧）

    LaunchedEffect(initialMessageId, initialMediaIdList) {
        // 用入参 ID 列表初始化，确保顺序与列表卡片缩略图一致
        // （Room @Relation 不保证 position 排序，而卡片渲染用的是 mediaList 的呈现顺序）
        val loaded = databaseManager.mediaRepository.getMediaByIds(initialMediaIdList)
            .associateBy { it.id }
        val finalList = initialMediaIdList.mapNotNull { loaded[it] }
        mediaList.clear()
        mediaMessageIds.clear()
        mediaList.addAll(finalList)
        repeat(finalList.size) { mediaMessageIds.add(initialMessageId) }
        isInitialized = true
    }

    if (!isInitialized || mediaList.isEmpty()) {
        LoadingBox()
        return
    }

    val startIndex = mediaList.indexOfFirst { it.id == initialMediaId }.coerceAtLeast(0)
    val pagerState = rememberPagerState(initialPage = startIndex) { mediaList.size }
    val stripListState = rememberLazyListState()

    // 当前 group 切片
    val currentMessageId = mediaMessageIds.getOrNull(pagerState.currentPage) ?: initialMessageId
    val groupRange = remember(currentMessageId, mediaMessageIds.size) {
        val start = mediaMessageIds.indexOfFirst { it == currentMessageId }
        val end = mediaMessageIds.indexOfLast { it == currentMessageId }
        if (start < 0) 0..0 else start..end
    }
    val pageInGroup = (pagerState.currentPage - groupRange.first).coerceAtLeast(0)
    val groupSize = (groupRange.last - groupRange.first + 1).coerceAtLeast(1)
    val groupMediaList = remember(groupRange, mediaList.size) {
        mediaList.subList(groupRange.first, groupRange.last + 1)
    }

    LaunchedEffect(pagerState.currentPage, groupRange) {
        // 居中当前缩略图（缩略图条内的索引 = pageInGroup）
        val viewportWidth = stripListState.layoutInfo.viewportSize.width
        val itemWidthPx =
            stripListState.layoutInfo.visibleItemsInfo.firstOrNull()?.size ?: viewportWidth
        val offset = -(viewportWidth / 2 - itemWidthPx / 2)
        stripListState.scrollToItem(index = pageInGroup, scrollOffset = offset)
    }

    // 边界扩展：MessageList 是 reverseLayout（最新在视觉底部）。
    // 用户视觉上「往右/下一张」= 进入更新的 message（createdAt 更大 = PREV）；
    // 「往左/上一张」= 进入更旧的 message（createdAt 更小 = NEXT）。
    LaunchedEffect(pagerState.currentPage) {
        if (isExpanding) return@LaunchedEffect

        val localIdx = pagerState.currentPage
        val distToEnd = mediaList.size - 1 - localIdx
        val distToStart = localIdx

        if (distToEnd < PRELOAD_THRESHOLD) {
            isExpanding = true
            try {
                val newerId = databaseManager.messageRepository.getAdjacentMessageIdWithMedia(
                    anchorMessageId = tailMessageId,
                    direction = MessageRepository.AdjacentDirection.PREV,
                    filter = filter
                )
                if (newerId != null) {
                    val moreMedia = databaseManager.messageRepository.getMediaByMessageId(newerId)
                    if (moreMedia.isNotEmpty()) {
                        mediaList.addAll(moreMedia)
                        repeat(moreMedia.size) { mediaMessageIds.add(newerId) }
                        tailMessageId = newerId
                    }
                }
            } finally {
                isExpanding = false
            }
        }

        if (distToStart < PRELOAD_THRESHOLD) {
            isExpanding = true
            try {
                val olderId = databaseManager.messageRepository.getAdjacentMessageIdWithMedia(
                    anchorMessageId = headMessageId,
                    direction = MessageRepository.AdjacentDirection.NEXT,
                    filter = filter
                )
                if (olderId != null) {
                    val moreMedia = databaseManager.messageRepository.getMediaByMessageId(olderId)
                    if (moreMedia.isNotEmpty()) {
                        mediaList.addAll(0, moreMedia)
                        repeat(moreMedia.size) { mediaMessageIds.add(0, olderId) }
                        headMessageId = olderId
                        // 维持视觉位置：插入了 N 条到头部，currentPage 向后偏移 N
                        pagerState.scrollToPage(pagerState.currentPage + moreMedia.size)
                    }
                }
            } finally {
                isExpanding = false
            }
        }
    }

    MediaViewerContent(
        mediaList = mediaList,
        pagerState = pagerState,
        stripListState = stripListState,
        totalCount = groupSize,
        currentGlobalIndex = pageInGroup,
        stripMediaList = groupMediaList,
        stripBaseIndex = groupRange.first,
        databaseManager = databaseManager,
        navController = navController,
        coroutineScope = coroutineScope
    )
}

/**
 * 浏览模式：使用传入的筛选后列表（适用于 media 页面切换收藏筛选后）
 * 直接使用筛选后的媒体列表，不需要窗口化分页
 */
@Composable
private fun BrowseModeViewer(
    initialMediaId: Long,
    initialMediaIdList: List<Long>,
    databaseManager: DatabaseManager,
    navController: NavController
) {
    val coroutineScope = rememberCoroutineScope()

    // 使用传入的筛选后列表
    val mediaList = remember { mutableStateListOf<Media>() }
    var isInitialized by remember { mutableStateOf(false) }
    var totalCount by remember { mutableIntStateOf(0) }

    // 初始化：加载传入的媒体列表
    LaunchedEffect(initialMediaId, initialMediaIdList) {
        if (initialMediaIdList.isEmpty()) {
            isInitialized = true
            return@LaunchedEffect
        }

        coroutineScope.launch {
            val loaded = databaseManager.mediaRepository.getMediaByIds(initialMediaIdList)
            val loadedMap = loaded.associateBy { it.id }
            // 按照传入顺序排列
            val ordered = initialMediaIdList.mapNotNull { loadedMap[it] }
            mediaList.clear()
            mediaList.addAll(ordered)
            totalCount = ordered.size
            isInitialized = true
        }
    }

    if (!isInitialized || mediaList.isEmpty()) {
        LoadingBox()
        return
    }

    // 找到初始媒体在列表中的位置
    val startIndex = mediaList.indexOfFirst { it.id == initialMediaId }.coerceAtLeast(0)
    val pagerState = rememberPagerState(initialPage = startIndex) { mediaList.size }
    val stripListState = rememberLazyListState()

    // 居中缩略图
    LaunchedEffect(pagerState.currentPage) {
        val viewportWidth = stripListState.layoutInfo.viewportSize.width
        val itemWidthPx =
            stripListState.layoutInfo.visibleItemsInfo.firstOrNull()?.size ?: viewportWidth
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
        totalCount = totalCount,
        currentGlobalIndex = pagerState.currentPage,
        databaseManager = databaseManager,
        navController = navController,
        coroutineScope = coroutineScope
    )
}

/**
 * 浏览模式：窗口化分页加载（适用于media页面的默认fallback无列表场景）
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
        val itemWidthPx =
            stripListState.layoutInfo.visibleItemsInfo.firstOrNull()?.size ?: viewportWidth
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
                val moreMedia =
                    databaseManager.mediaRepository.getMediaWindow(currentEnd, loadCount)
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
    coroutineScope: kotlinx.coroutines.CoroutineScope,
    stripMediaList: List<Media> = mediaList,
    stripBaseIndex: Int = 0
) {
    // 用于收藏状态变更的可变列表引用
    val mutableMediaList = mediaList as? MutableList<Media>

    // 图片缩放状态 — 控制 Pager 是否允许滑动
    var currentScale by remember { mutableFloatStateOf(1f) }

    // 顶部栏 + 底部缩略图条的显隐（仅由图片单击翻转，不受视频自动隐藏影响）
    var stripVisible by remember { mutableStateOf(true) }

    // 视频内部控件（进度条/播放按钮）的显隐，沿用 3s 自动隐藏
    var videoControlsVisible by remember { mutableStateOf(false) }

    // 切换页面时重置缩放状态，并清掉视频控件可见态避免跨页继承
    LaunchedEffect(pagerState.settledPage) {
        currentScale = 1f
        videoControlsVisible = false
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .systemBarsPadding()
    ) {
        HorizontalPager(
            state = pagerState,
            modifier = Modifier.fillMaxSize(),
            beyondViewportPageCount = 0, // 只保留当前页的 ExoPlayer，避免 OOM
            userScrollEnabled = currentScale <= 1f
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
                            .padding(bottom = if (mediaList.size > 1) 76.dp else 0.dp),
                        zoomEnabled = true,
                        controlsVisible = videoControlsVisible,
                        onScaleChanged = { if (isCurrentPage) currentScale = it },
                        onControlsVisibilityChanged = { visible ->
                            if (isCurrentPage) videoControlsVisible = visible
                        }
                    )
                } else {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text("无法加载视频", color = Color.White)
                    }
                }
            } else {
                val imagePath = media.filePath ?: media.thumbnailPath
                ZoomableImage(
                    imagePath = imagePath,
                    onScaleChanged = { if (isCurrentPage) currentScale = it },
                    modifier = Modifier.fillMaxSize(),
                    onSingleTap = { stripVisible = !stripVisible }
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
                val idx = pagerState.currentPage.coerceIn(0, mediaList.size - 1)
                val currentMedia = mediaList[idx]
                val starred = currentMedia.starred
                IconButton(onClick = {
                    val targetId = currentMedia.id
                    val newStarred = !starred
                    mutableMediaList?.let {
                        if (idx in it.indices && it[idx].id == targetId) {
                            it[idx] = it[idx].copy(starred = newStarred)
                        }
                    }
                    coroutineScope.launch {
                        databaseManager.mediaRepository.toggleMediaStarred(targetId)
                    }
                }) {
                    Icon(
                        imageVector = if (starred) Icons.Filled.Star else Icons.Outlined.Star,
                        contentDescription = if (starred) "取消收藏" else "收藏",
                        tint = if (starred) Color(0xFFFFD700) else Color.White
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

        // 底部：横向缩略图导航条（多于1个媒体时显示，受 stripVisible 控制）
        if (stripMediaList.size > 1) {
            AnimatedVisibility(
                visible = stripVisible,
                enter = fadeIn(),
                exit = fadeOut(),
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
            ) {
                MediaStripBar(
                    mediaList = stripMediaList,
                    currentIndex = (pagerState.currentPage - stripBaseIndex)
                        .coerceIn(0, stripMediaList.size - 1),
                    listState = stripListState,
                    pagerState = pagerState,
                    baseIndex = stripBaseIndex
                )
            }
        }
    }
}

@Composable
private fun MediaStripBar(
    mediaList: List<Media>,
    currentIndex: Int,
    listState: androidx.compose.foundation.lazy.LazyListState,
    pagerState: androidx.compose.foundation.pager.PagerState,
    modifier: Modifier = Modifier,
    baseIndex: Int = 0
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
                            if (isSelected) Modifier.border(
                                2.dp,
                                Color.White,
                                RoundedCornerShape(4.dp)
                            )
                            else Modifier
                        )
                        .clip(RoundedCornerShape(4.dp))
                        .clickable {
                            coroutineScope.launch {
                                pagerState.animateScrollToPage(baseIndex + index)
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
                                .background(
                                    Color.Black.copy(alpha = 0.6f),
                                    RoundedCornerShape(2.dp)
                                ),
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
