package com.example.myapplication.ui.screens.message

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.platform.LocalContext
import androidx.paging.LoadState
import androidx.paging.compose.collectAsLazyPagingItems
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.ui.components.*
import com.example.myapplication.ui.theme.InstagramGradientMiddle
import com.example.myapplication.ui.viewmodel.MessageViewModel
import com.example.myapplication.ui.viewmodel.UIState
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

/**
 * Telegram 风格消息列表页面
 *
 * 布局结构（从上到下）：
 *   statusBarsPadding
 *   搜索栏（固定，不随键盘移动）
 *   Box（weight=1f, imePadding）
 *     ├─ LazyColumn（消息流）
 *     └─ MessageComposeBar（底部对齐）
 *   navigationBarsPadding
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MessageListScreen(
    viewModel: MessageViewModel,
    databaseManager: DatabaseManager,
    onMessageClick: (Long) -> Unit = { },
    onEditMessage: (Long) -> Unit = { },
    onMediaClick: (mediaId: Long, messageId: Long, mediaList: List<Media>) -> Unit = { _, _, _ -> },
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState(initial = UIState())
    val pagingItems = viewModel.messagesPaged.collectAsLazyPagingItems()
    val searchQuery by viewModel.searchQuery.collectAsState(initial = "")
    val isSending by viewModel.isSending.collectAsState()

    var snackbarMessage by remember { mutableStateOf<String?>(null) }
    val snackbarHostState = remember { SnackbarHostState() }
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()

    // reverseLayout=true 时，firstVisibleItemIndex==0 表示已在最新消息（视觉底部）
    val showScrollToBottom by remember {
        derivedStateOf { listState.firstVisibleItemIndex > 2 }
    }

    // 日期格式化
    val dateFormatter = remember { SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()) }

    // 显示 Snackbar 消息
    LaunchedEffect(snackbarMessage) {
        snackbarMessage?.let { message ->
            snackbarHostState.showSnackbar(message)
            snackbarMessage = null
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface)
            .statusBarsPadding()
    ) {
        // 固定顶部搜索栏 — 不受键盘影响
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surface)
                .padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            SearchBar(
                query = searchQuery,
                onQueryChanged = viewModel::searchMessages,
                placeholder = "搜索消息...",
                modifier = Modifier.weight(1f)
            )
        }

        // 消息流 + 输入框放在同一个 Box 里，一起响应键盘
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .imePadding()
                .navigationBarsPadding()
        ) {
            val refreshState = pagingItems.loadState.refresh

            when {
                refreshState is LoadState.Loading && pagingItems.itemCount == 0 -> {
                    LoadingIndicator()
                }

                refreshState is LoadState.Error && pagingItems.itemCount == 0 -> {
                    EmptyState(message = "加载失败: ${refreshState.error.localizedMessage}")
                }

                refreshState is LoadState.NotLoading && pagingItems.itemCount == 0 -> {
                    EmptyState(
                        message = if (searchQuery.isNotBlank()) {
                            "没有找到符合条件的消息"
                        } else {
                            "暂无消息数据\n在下方输入消息发送"
                        }
                    )
                }

                else -> {
                    // Telegram 风格：reverseLayout 让最新消息在底部
                    LazyColumn(
                        state = listState,
                        reverseLayout = true,
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        contentPadding = PaddingValues(
                            top = 8.dp,
                            // 底部留出输入框的空间（约 60dp）
                            bottom = 64.dp,
                            start = 8.dp,
                            end = 8.dp
                        )
                    ) {
                        // 发送中占位卡片（reverseLayout 中排在最前 = 视觉最底部）
                        if (isSending) {
                            item(key = "sending_placeholder") {
                                SendingPlaceholderCard()
                            }
                        }

                        items(
                            count = pagingItems.itemCount,
                            key = { index -> pagingItems[index]?.message?.id ?: index }
                        ) { index ->
                            val item = pagingItems[index]
                            if (item != null) {
                                // 日期分隔符：比较当前和下一条（index+1 方向是更旧的）
                                val currentDate = dateFormatter.format(Date(item.message.createdAt))
                                val nextItem = if (index + 1 < pagingItems.itemCount) pagingItems[index + 1] else null
                                val nextDate = nextItem?.let { dateFormatter.format(Date(it.message.createdAt)) }

                                // 在 reverseLayout 中，index+1 是视觉上方（更旧的消息）
                                // 当日期不同时，在当前消息上方显示日期分隔符
                                if (nextDate != null && currentDate != nextDate) {
                                    DateSeparator(date = currentDate)
                                }
                                // 最旧的一条也显示日期
                                if (nextDate == null && index == pagingItems.itemCount - 1) {
                                    DateSeparator(date = currentDate)
                                }

                                MessageCard(
                                    messageWithDetails = item,
                                    onMediaClick = { mediaId, mediaList -> onMediaClick(mediaId, item.message.id, mediaList) },
                                    onEditClick = { onEditMessage(it) },
                                    onDeleteClick = { viewModel.deleteMessage(it) },
                                    onToggleStarred = { viewModel.toggleStarred(it) },
                                    onRetrySync = { viewModel.retrySync(it) },
                                    modifier = Modifier.fillMaxWidth()
                                )
                            }
                        }

                        // 顶部加载更多指示器（在 reverse 模式下是视觉顶部 = 列表底部）
                        if (pagingItems.loadState.append is LoadState.Loading) {
                            item {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(16.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(24.dp),
                                        strokeWidth = 2.dp,
                                        color = InstagramGradientMiddle
                                    )
                                }
                            }
                        }
                    }
                }
            }

            // 输入栏固定在 Box 底部，与消息流叠加
            MessageComposeBar(
                onSendMessage = { text, mediaList ->
                    viewModel.sendMessage(
                        text = text,
                        mediaList = mediaList,
                        databaseManager = databaseManager,
                        context = context,
                        onSuccess = { },
                        onError = { }
                    )
                    // 立即滚动到占位卡片
                    coroutineScope.launch { listState.animateScrollToItem(0) }
                },
                isSending = isSending,
                modifier = Modifier.align(Alignment.BottomCenter)
            )

            // Snackbar
            SnackbarHost(
                hostState = snackbarHostState,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(bottom = 64.dp)
            )

            // 滚动到底部按钮
            if (showScrollToBottom) {
                SmallFloatingActionButton(
                    onClick = { coroutineScope.launch { listState.scrollToItem(0) } },
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(end = 12.dp, bottom = 72.dp),
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                    shape = CircleShape
                ) {
                    Icon(
                        imageVector = Icons.Default.KeyboardArrowDown,
                        contentDescription = "滚动到底部"
                    )
                }
            }
        }
    }

    // 错误消息处理
    uiState.error?.let { error ->
        LaunchedEffect(error) {
            snackbarMessage = error
            viewModel.clearError()
        }
    }

    // 成功消息处理
    uiState.message?.let { message ->
        LaunchedEffect(message) {
            snackbarMessage = message
            viewModel.clearMessage()
        }
    }
}

/**
 * 发送中占位卡片 — 消息正在预处理时显示
 */
@Composable
private fun SendingPlaceholderCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceContainer
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 20.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            CircularProgressIndicator(
                modifier = Modifier.size(16.dp),
                strokeWidth = 2.dp,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "正在准备消息...",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
            )
        }
    }
}

/**
 * 日期分隔符组件 (Telegram 风格)
 */
@Composable
private fun DateSeparator(
    date: String,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.7f)
        ) {
            Text(
                text = date,
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontSize = 12.sp,
                fontWeight = FontWeight.Medium
            )
        }
    }
}
