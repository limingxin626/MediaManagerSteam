package com.example.myapplication.ui.components

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
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.PagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
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
import com.example.myapplication.ui.model.ViewerMediaItem
import kotlinx.coroutines.launch

@Composable
fun SharedMediaViewer(
    items: List<ViewerMediaItem>,
    pagerState: PagerState,
    stripListState: LazyListState,
    totalCount: Int,
    globalIndexOffset: Int = 0,
    onClose: () -> Unit,
    modifier: Modifier = Modifier,
    stripItems: List<ViewerMediaItem> = items,
    stripBaseIndex: Int = 0,
    onToggleStar: ((page: Int) -> Unit)? = null,
    onEditTags: ((page: Int) -> Unit)? = null
) {
    var currentScale by remember { mutableFloatStateOf(1f) }
    var stripVisible by remember { mutableStateOf(true) }
    var videoControlsVisible by remember { mutableStateOf(false) }

    LaunchedEffect(pagerState.settledPage) {
        currentScale = 1f
        videoControlsVisible = false
    }

    LaunchedEffect(pagerState.currentPage, stripBaseIndex, stripItems.size) {
        if (stripItems.isEmpty()) return@LaunchedEffect
        val stripIndex = (pagerState.currentPage - stripBaseIndex)
            .coerceIn(0, stripItems.lastIndex)
        val viewportWidth = stripListState.layoutInfo.viewportSize.width
        val itemWidth = stripListState.layoutInfo.visibleItemsInfo.firstOrNull()?.size
            ?: viewportWidth
        stripListState.scrollToItem(
            index = stripIndex,
            scrollOffset = -(viewportWidth / 2 - itemWidth / 2)
        )
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.Black)
            .systemBarsPadding()
    ) {
        HorizontalPager(
            state = pagerState,
            key = { index -> "${items[index].key}:$index" },
            modifier = Modifier.fillMaxSize(),
            beyondViewportPageCount = 0,
            userScrollEnabled = currentScale <= 1f
        ) { page ->
            val item = items[page]
            val isCurrentPage = pagerState.settledPage == page
            if (item.isVideo) {
                val path = item.mediaUri
                if (path != null) {
                    TelegramVideoPlayer(
                        videoPath = path,
                        autoPlay = isCurrentPage,
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(bottom = if (stripItems.size > 1) 76.dp else 0.dp),
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
                ZoomableImage(
                    imagePath = item.mediaUri ?: item.thumbnailUri,
                    onScaleChanged = { if (isCurrentPage) currentScale = it },
                    modifier = Modifier.fillMaxSize(),
                    onSingleTap = { stripVisible = !stripVisible }
                )
            }
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.TopCenter)
                .padding(horizontal = 8.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onClose) {
                Icon(
                    imageVector = Icons.Default.Close,
                    contentDescription = "关闭",
                    tint = Color.White,
                    modifier = Modifier.size(28.dp)
                )
            }
            Spacer(Modifier.weight(1f))

            val currentItem = items.getOrNull(pagerState.currentPage)
            if (onEditTags != null && currentItem != null) {
                IconButton(onClick = { onEditTags(pagerState.currentPage) }) {
                    Icon(
                        imageVector = Icons.Default.MoreVert,
                        contentDescription = "编辑标签",
                        tint = Color.White
                    )
                }
            }
            if (onToggleStar != null && currentItem?.starred != null) {
                IconButton(onClick = { onToggleStar(pagerState.currentPage) }) {
                    Icon(
                        imageVector = if (currentItem.starred) Icons.Filled.Star else Icons.Outlined.Star,
                        contentDescription = if (currentItem.starred) "取消收藏" else "收藏",
                        tint = if (currentItem.starred) Color(0xFFFFD700) else Color.White
                    )
                }
            }

            if (totalCount > 1) {
                Text(
                    text = "${globalIndexOffset + pagerState.currentPage + 1} / $totalCount",
                    color = Color.White,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.padding(end = 16.dp)
                )
            }
        }

        if (stripItems.size > 1) {
            AnimatedVisibility(
                visible = stripVisible,
                enter = fadeIn(),
                exit = fadeOut(),
                modifier = Modifier.align(Alignment.BottomCenter).fillMaxWidth()
            ) {
                ViewerMediaStrip(
                    items = stripItems,
                    currentIndex = (pagerState.currentPage - stripBaseIndex)
                        .coerceIn(0, stripItems.lastIndex),
                    listState = stripListState,
                    pagerState = pagerState,
                    baseIndex = stripBaseIndex
                )
            }
        }
    }
}

@Composable
private fun ViewerMediaStrip(
    items: List<ViewerMediaItem>,
    currentIndex: Int,
    listState: LazyListState,
    pagerState: PagerState,
    baseIndex: Int,
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
            itemsIndexed(items, key = { index, item -> "${item.key}:$index" }) { index, item ->
                val selected = index == currentIndex
                Box(
                    modifier = Modifier
                        .size(60.dp)
                        .then(
                            if (selected) Modifier.border(
                                2.dp,
                                Color.White,
                                RoundedCornerShape(4.dp)
                            ) else Modifier
                        )
                        .clip(RoundedCornerShape(4.dp))
                        .clickable {
                            coroutineScope.launch {
                                pagerState.animateScrollToPage(baseIndex + index)
                            }
                        }
                ) {
                    OptimizedThumbnail(
                        thumbnailPath = item.thumbnailUri ?: item.mediaUri,
                        modifier = Modifier.fillMaxSize()
                    )
                    if (item.isVideo) {
                        Box(
                            modifier = Modifier
                                .size(16.dp)
                                .align(Alignment.BottomEnd)
                                .padding(2.dp)
                                .background(Color.Black.copy(alpha = 0.6f), RoundedCornerShape(2.dp)),
                            contentAlignment = Alignment.Center
                        ) {
                            androidx.compose.foundation.Canvas(Modifier.size(8.dp)) {
                                val path = androidx.compose.ui.graphics.Path().apply {
                                    moveTo(0f, 0f)
                                    lineTo(size.width, size.height / 2f)
                                    lineTo(0f, size.height)
                                    close()
                                }
                                drawPath(path, Color.White)
                            }
                        }
                    }
                    if (!selected) {
                        Box(Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.35f)))
                    }
                }
            }
        }
    }
}
