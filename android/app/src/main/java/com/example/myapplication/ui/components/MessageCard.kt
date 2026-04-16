package com.example.myapplication.ui.components

import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.Message
import com.example.myapplication.data.database.entities.MessageWithDetails
import com.example.myapplication.data.database.entities.Tag
import com.example.myapplication.ui.theme.TextSecondary
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Telegram 风格消息卡片组件
 */
@OptIn(ExperimentalFoundationApi::class, ExperimentalLayoutApi::class)
@Composable
fun MessageCard(
    messageWithDetails: MessageWithDetails,
    modifier: Modifier = Modifier,
    onMediaClick: (mediaId: Long, mediaList: List<Media>) -> Unit = { _, _ -> },
    onEditClick: (Long) -> Unit = {},
    onDeleteClick: (Long) -> Unit = {},
    onToggleStarred: (Long) -> Unit = {},
    onRetrySync: ((Long) -> Unit)? = null
) {
    val message = messageWithDetails.message
    val mediaList = messageWithDetails.mediaList
    val actor = messageWithDetails.actor

    val dateFormatter = remember { SimpleDateFormat("HH:mm", Locale.getDefault()) }
    val formattedTime = remember(message.createdAt) {
        dateFormatter.format(Date(message.createdAt))
    }

    var showMenu by remember { mutableStateOf(false) }

    // 单图时计算卡片宽度，使卡片收缩到图片宽度（Telegram 风格）
    val screenWidthDp = LocalConfiguration.current.screenWidthDp.dp
    val maxCardWidth = screenWidthDp * 0.9f
    val singleImageMaxHeight = 360.dp

    val cardWidthModifier = if (mediaList.size == 1) {
        val media0 = mediaList[0]
        val aspectRatio =
            if (media0.width != null && media0.height != null && media0.width > 0 && media0.height > 0) {
                media0.width.toFloat() / media0.height.toFloat()
            } else {
                1f
            }
        val minRatio = 9f / 16f  // 比 9:16 更窄的图片会被裁剪
        val clampedRatio = aspectRatio.coerceIn(minRatio, 2.5f)
        val naturalWidth = (singleImageMaxHeight * clampedRatio).coerceAtMost(maxCardWidth)
        val cardWidth = naturalWidth
        Modifier.width(cardWidth)
    } else {
        Modifier.fillMaxWidth(0.9f)
    }

    Box(modifier = modifier) {
        Card(
            modifier = cardWidthModifier
                .combinedClickable(
                    onClick = {},
                    onLongClick = { showMenu = true }
                ),
            shape = RoundedCornerShape(8.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceContainer
            )
        ) {
            Column(modifier = Modifier.fillMaxWidth()) {
                // 缩略图网格区域
                if (mediaList.isNotEmpty()) {
                    MediaThumbnailGrid(
                        mediaList = mediaList,
                        messageId = message.id,
                        onMediaClick = { mediaId -> onMediaClick(mediaId, mediaList) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(topStart = 8.dp, topEnd = 8.dp))
                    )
                }

                // 文本和元信息
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 8.dp)
                ) {
                    // 消息文本内容（#tag 高亮）
                    if (!message.text.isNullOrBlank()) {
                        val defaultTagColor = MaterialTheme.colorScheme.primary
                        val annotatedText = remember(message.text, messageWithDetails.tagList) {
                            buildHighlightedTagText(
                                message.text,
                                messageWithDetails.tagList,
                                defaultTagColor
                            )
                        }
                        Text(
                            text = annotatedText,
                            style = MaterialTheme.typography.bodyMedium,
                            maxLines = 3,
                            overflow = TextOverflow.Ellipsis,
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                    }

                    // Tag chips
                    if (messageWithDetails.tagList.isNotEmpty()) {
                        val defaultTagColor = MaterialTheme.colorScheme.primary
                        FlowRow(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            messageWithDetails.tagList.forEach { tag ->
                                val chipColor = tag.color?.let { parseColor(it) } ?: defaultTagColor
                                Surface(
                                    shape = CircleShape,
                                    color = chipColor.copy(alpha = 0.15f),
                                    modifier = Modifier.height(22.dp)
                                ) {
                                    Text(
                                        text = "#${tag.name}",
                                        style = MaterialTheme.typography.labelSmall.copy(
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Medium
                                        ),
                                        color = chipColor,
                                        modifier = Modifier.padding(
                                            horizontal = 8.dp,
                                            vertical = 2.dp
                                        )
                                    )
                                }
                            }
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                    }

                    // 底部元信息行
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // 左侧：根据 sendStatus 显示不同内容
                        when (message.sendStatus) {
                            Message.MSG_STATUS_PUSHING -> {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(12.dp),
                                        strokeWidth = 1.5.dp,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                    Text(
                                        text = "同步中...",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = TextSecondary,
                                        fontSize = 12.sp
                                    )
                                }
                            }

                            Message.MSG_STATUS_PUSH_FAILED -> {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Text(
                                        text = "同步失败",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.error,
                                        fontSize = 12.sp
                                    )
                                    if (onRetrySync != null) {
                                        Text(
                                            text = "· 重试",
                                            style = MaterialTheme.typography.labelSmall.copy(
                                                fontWeight = FontWeight.SemiBold
                                            ),
                                            color = MaterialTheme.colorScheme.primary,
                                            fontSize = 12.sp,
                                            modifier = Modifier.clickable { onRetrySync(message.id) }
                                        )
                                    }
                                }
                            }

                            else -> {
                                // SYNCED: 正常显示演员名 + 时间
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    if (actor != null) {
                                        Text(
                                            text = actor.name,
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.primary,
                                            fontWeight = FontWeight.Medium,
                                            fontSize = 12.sp
                                        )
                                        Text(
                                            text = "·",
                                            style = MaterialTheme.typography.labelSmall,
                                            color = TextSecondary,
                                            fontSize = 12.sp
                                        )
                                    }
                                    Text(
                                        text = formattedTime,
                                        style = MaterialTheme.typography.labelSmall,
                                        color = TextSecondary,
                                        fontSize = 12.sp
                                    )
                                }
                            }
                        }

                        // 右侧：收藏图标
                        if (message.starred) {
                            StarIcon(
                                isStarred = true,
                                size = 14.dp,
                                tint = MaterialTheme.colorScheme.primary
                            )
                        }
                    }
                }
            }
        }

        // 长按上下文菜单
        DropdownMenu(
            expanded = showMenu,
            onDismissRequest = { showMenu = false }
        ) {
            DropdownMenuItem(
                text = { Text("编辑") },
                onClick = {
                    showMenu = false
                    onEditClick(message.id)
                },
                leadingIcon = {
                    Icon(Icons.Default.Edit, contentDescription = null)
                }
            )
            DropdownMenuItem(
                text = { Text(if (message.starred) "取消收藏" else "收藏") },
                onClick = {
                    showMenu = false
                    onToggleStarred(message.id)
                },
                leadingIcon = {
                    Icon(
                        if (message.starred) Icons.Filled.Star else Icons.Outlined.Star,
                        contentDescription = null
                    )
                }
            )
            DropdownMenuItem(
                text = { Text("删除", color = MaterialTheme.colorScheme.error) },
                onClick = {
                    showMenu = false
                    onDeleteClick(message.id)
                },
                leadingIcon = {
                    Icon(
                        Icons.Default.Delete,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.error
                    )
                }
            )
        }
    }
}

/**
 * 媒体缩略图网格 — 使用 Telegram 风格 Mosaic 布局
 */
@Composable
private fun MediaThumbnailGrid(
    mediaList: List<Media>,
    messageId: Long,
    onMediaClick: (Long) -> Unit,
    modifier: Modifier = Modifier
) {
    val displayMedia = mediaList.take(10)
    val extraCount = (mediaList.size - 10).coerceAtLeast(0)

    if (displayMedia.size == 1) {
        // 单图：保持原始比例，高度不超过 360dp
        val media0 = displayMedia[0]
        val aspectRatio =
            if (media0.width != null && media0.height != null && media0.width > 0 && media0.height > 0) {
                media0.width.toFloat() / media0.height.toFloat()
            } else {
                1f
            }
        val clampedRatio = aspectRatio.coerceIn(9f / 16f, 2.5f)
        val density = androidx.compose.ui.platform.LocalDensity.current
        var widthPx by remember(media0.id) { mutableStateOf(0) }
        val maxHeightDp = 360.dp
        val maxHeightPx = with(density) { maxHeightDp.toPx() }
        val effectiveWidthPx =
            if (widthPx > 0) widthPx.toFloat() else maxHeightPx * clampedRatio
        val naturalHeightPx = effectiveWidthPx / clampedRatio
        val finalHeightPx = naturalHeightPx.coerceAtMost(maxHeightPx)
        val finalWidthPx = (finalHeightPx * clampedRatio).coerceAtMost(effectiveWidthPx)
        val finalHeightDp = with(density) { finalHeightPx.toDp() }
        val finalWidthDp = with(density) { finalWidthPx.toDp() }
        Box(
            modifier = modifier.onGloballyPositioned { widthPx = it.size.width }
        ) {
            MediaThumbnailItem(
                media = media0,
                messageId = messageId,
                onClick = { onMediaClick(media0.id) },
                modifier = Modifier.size(width = finalWidthDp, height = finalHeightDp)
            )
        }
        return
    }

    // 2-10 图：Mosaic 动态布局
    val ratios = remember(displayMedia) {
        displayMedia.map { media ->
            if (media.width != null && media.height != null && media.width > 0 && media.height > 0) {
                media.width.toFloat() / media.height.toFloat()
            } else {
                1f
            }
        }
    }

    val density = androidx.compose.ui.platform.LocalDensity.current
    var containerWidthPx by remember { mutableStateOf(0f) }
    val layout = remember(ratios, containerWidthPx) {
        calculateMosaicLayout(ratios, if (containerWidthPx > 0f) containerWidthPx else 400f)
    }

    // 计算总高度（px），然后转 dp
    // ROWS: heightWeight 是每行的像素高度（containerWidth / 行内比例之和）
    // LEFT_COLUMN: 高度由左列图片决定
    val totalHeightPx = remember(layout, containerWidthPx) {
        if (containerWidthPx <= 0f) return@remember 300f * density.density
        if (layout.type == MosaicType.ROWS) {
            val gapPx = 2f * density.density * (layout.rows.size - 1).coerceAtLeast(0)
            layout.rows.sumOf { it.heightWeight.toDouble() }.toFloat() + gapPx
        } else {
            val leftWidthPx = containerWidthPx * layout.leftColumnWidth
            val leftRatio = ratios[layout.leftColumnIndex].coerceIn(0.667f, 1.7f)
            leftWidthPx / leftRatio
        }
    }
    val maxHeightPx = with(density) { 800.dp.toPx() }
    val minHeightPx = with(density) { 120.dp.toPx() }
    val clampedHeightPx = totalHeightPx.coerceIn(minHeightPx, maxHeightPx)
    val totalHeightDpVal = with(density) { clampedHeightPx.toDp() }

    Box(
        modifier = modifier.onGloballyPositioned {
            containerWidthPx = it.size.width.toFloat()
        }
    ) {
        when (layout.type) {
            MosaicType.ROWS -> {
                MosaicRowsGrid(
                    layout = layout,
                    displayMedia = displayMedia,
                    extraCount = extraCount,
                    messageId = messageId,
                    onMediaClick = onMediaClick,
                    modifier = Modifier.height(totalHeightDpVal)
                )
            }
            MosaicType.LEFT_COLUMN -> {
                MosaicLeftColumnGrid(
                    layout = layout,
                    displayMedia = displayMedia,
                    extraCount = extraCount,
                    messageId = messageId,
                    onMediaClick = onMediaClick,
                    modifier = Modifier.height(totalHeightDpVal)
                )
            }
        }
    }
}

/**
 * 纯行布局渲染（ROWS 类型）
 */
@Composable
private fun MosaicRowsGrid(
    layout: MosaicLayout,
    displayMedia: List<Media>,
    extraCount: Int,
    messageId: Long,
    onMediaClick: (Long) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        layout.rows.forEachIndexed { rowIndex, row ->
            if (rowIndex > 0) Spacer(modifier = Modifier.height(2.dp))
            Row(modifier = Modifier.weight(row.heightWeight)) {
                row.items.forEachIndexed { colIndex, item ->
                    if (colIndex > 0) Spacer(modifier = Modifier.width(2.dp))
                    val media = displayMedia[item.index]
                    val isLast = item.index == displayMedia.lastIndex && extraCount > 0
                    if (isLast) {
                        OverflowCell(
                            media = media,
                            extraCount = extraCount,
                            messageId = messageId,
                            onMediaClick = onMediaClick,
                            modifier = Modifier.weight(item.widthWeight).fillMaxHeight()
                        )
                    } else {
                        MediaThumbnailItem(
                            media = media,
                            messageId = messageId,
                            onClick = { onMediaClick(media.id) },
                            modifier = Modifier.weight(item.widthWeight).fillMaxHeight()
                        )
                    }
                }
            }
        }
    }
}

/**
 * 左列大图 + 右列多行布局渲染（LEFT_COLUMN 类型）
 */
@Composable
private fun MosaicLeftColumnGrid(
    layout: MosaicLayout,
    displayMedia: List<Media>,
    extraCount: Int,
    messageId: Long,
    onMediaClick: (Long) -> Unit,
    modifier: Modifier = Modifier
) {
    val leftMedia = displayMedia[layout.leftColumnIndex]

    Row(modifier = modifier) {
        // 左列大图
        MediaThumbnailItem(
            media = leftMedia,
            messageId = messageId,
            onClick = { onMediaClick(leftMedia.id) },
            modifier = Modifier
                .weight(layout.leftColumnWidth)
                .fillMaxHeight()
        )
        Spacer(modifier = Modifier.width(2.dp))
        // 右列多行
        Column(
            modifier = Modifier
                .weight(1f - layout.leftColumnWidth)
                .fillMaxHeight()
        ) {
            layout.rows.forEachIndexed { rowIndex, row ->
                if (rowIndex > 0) Spacer(modifier = Modifier.height(2.dp))
                Row(modifier = Modifier.weight(row.heightWeight)) {
                    row.items.forEachIndexed { colIndex, item ->
                        if (colIndex > 0) Spacer(modifier = Modifier.width(2.dp))
                        val media = displayMedia[item.index]
                        val isLast = item.index == displayMedia.lastIndex && extraCount > 0
                        if (isLast) {
                            OverflowCell(
                                media = media,
                                extraCount = extraCount,
                                messageId = messageId,
                                onMediaClick = onMediaClick,
                                modifier = Modifier.weight(item.widthWeight).fillMaxHeight()
                            )
                        } else {
                            MediaThumbnailItem(
                                media = media,
                                messageId = messageId,
                                onClick = { onMediaClick(media.id) },
                                modifier = Modifier.weight(item.widthWeight).fillMaxHeight()
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * "+N" 溢出显示单元格
 */
@Composable
private fun OverflowCell(
    media: Media,
    extraCount: Int,
    messageId: Long,
    onMediaClick: (Long) -> Unit,
    modifier: Modifier = Modifier
) {
    Box(modifier = modifier) {
        MediaThumbnailItem(
            media = media,
            messageId = messageId,
            onClick = { onMediaClick(media.id) },
            modifier = Modifier.fillMaxSize()
        )
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.5f)),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "+$extraCount",
                color = Color.White,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

/**
 * 单个媒体缩略图项
 */
@Composable
private fun MediaThumbnailItem(
    media: Media,
    messageId: Long,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isVideo = remember(media.mimeType) { media.mimeType?.startsWith("video/") == true }
    val durationText = remember(media.durationMs) {
        media.durationMs?.let { ms ->
            val totalSeconds = ms / 1000
            "${totalSeconds / 60}:${String.format("%02d", totalSeconds % 60)}"
        }
    }

    Box(modifier = modifier.clickable { onClick() }) {
        OptimizedThumbnail(
            thumbnailPath = media.thumbnailPath ?: media.filePath,
            modifier = Modifier.fillMaxSize()
        )

        // 收藏标记 - 右上角
        if (media.starred) {
            Icon(
                imageVector = Icons.Filled.Star,
                contentDescription = "已收藏",
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(4.dp)
                    .size(14.dp),
                tint = Color(0xFFFFD700)
            )
        }

        if (isVideo) {
            // 底部渐变遮罩
            if (durationText != null) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(32.dp)
                        .align(Alignment.BottomCenter)
                        .background(
                            Brush.verticalGradient(
                                colors = listOf(Color.Transparent, Color.Black.copy(alpha = 0.5f))
                            )
                        )
                )
            }

            // 播放图标
            Box(
                modifier = Modifier
                    .align(Alignment.Center)
                    .size(32.dp)
                    .background(Color.Black.copy(alpha = 0.4f), RoundedCornerShape(16.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.PlayArrow,
                    contentDescription = "播放",
                    modifier = Modifier.size(18.dp),
                    tint = Color.White
                )
            }

            // 时长标签
            if (durationText != null) {
                Text(
                    text = durationText,
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(4.dp),
                    style = MaterialTheme.typography.labelSmall.copy(
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Medium
                    ),
                    color = Color.White
                )
            }
        }
    }
}

/**
 * 星星图标组件
 */
@Composable
fun StarIcon(
    isStarred: Boolean,
    size: androidx.compose.ui.unit.Dp = 20.dp,
    tint: Color = MaterialTheme.colorScheme.onSurface
) {
    val icon = if (isStarred) {
        Icons.Filled.Star
    } else {
        Icons.Outlined.Star
    }

    Icon(
        imageVector = icon,
        contentDescription = if (isStarred) "已收藏" else "未收藏",
        modifier = Modifier.size(size),
        tint = tint
    )
}

private val TAG_HIGHLIGHT_PATTERN = Regex("""#([\w\u4e00-\u9fff\u3400-\u4dbf-]+)""")

private fun parseColor(colorStr: String): Color? {
    return try {
        Color(android.graphics.Color.parseColor(colorStr))
    } catch (_: Exception) {
        null
    }
}

/**
 * 构建带 #tag 高亮的 AnnotatedString，优先使用 Tag 自身的 color
 */
private fun buildHighlightedTagText(
    text: String,
    tagList: List<Tag>,
    defaultColor: Color
) = buildAnnotatedString {
    val tagColorMap = tagList.associate { tag ->
        tag.name to (tag.color?.let { parseColor(it) } ?: defaultColor)
    }
    var cursor = 0
    TAG_HIGHLIGHT_PATTERN.findAll(text).forEach { match ->
        val tagName = match.groupValues[1]
        val color = tagColorMap[tagName] ?: defaultColor
        // 普通文本
        if (match.range.first > cursor) {
            append(text.substring(cursor, match.range.first))
        }
        // #tag 高亮
        withStyle(SpanStyle(color = color, fontWeight = FontWeight.Medium)) {
            append(match.value)
        }
        cursor = match.range.last + 1
    }
    // 剩余普通文本
    if (cursor < text.length) {
        append(text.substring(cursor))
    }
}
