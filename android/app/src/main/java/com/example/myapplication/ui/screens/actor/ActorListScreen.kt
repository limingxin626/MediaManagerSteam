package com.example.myapplication.ui.screens.actor

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
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
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.platform.LocalDensity
import kotlin.math.roundToInt
import com.example.myapplication.LocalBottomBarVisible
import com.example.myapplication.data.database.entities.Actor
import com.example.myapplication.ui.components.*
import com.example.myapplication.ui.components.ActorCard
import com.example.myapplication.ui.theme.InstagramGradientEnd
import com.example.myapplication.ui.theme.InstagramGradientMiddle
import com.example.myapplication.ui.theme.InstagramGradientStart
import com.example.myapplication.ui.theme.TextSecondary
import com.example.myapplication.ui.viewmodel.ActorViewModel
import com.example.myapplication.ui.viewmodel.ActorSortBy

/**
 * Instagram 风格演员列表页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ActorListScreen(
    viewModel: ActorViewModel,
    onActorClick: (Actor) -> Unit = {},
    onAddActor: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    // Instagram 渐变色
    val instagramGradient = Brush.linearGradient(
        colors = listOf(
            InstagramGradientStart, InstagramGradientMiddle, InstagramGradientEnd
        )
    )

    // 优化状态收集，减少不必要的重组
    val uiState by viewModel.uiState.collectAsState()
    val actors by viewModel.actors.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    val selectedCountry by viewModel.selectedCountry.collectAsState()
    val selectedCategory by viewModel.selectedCategory.collectAsState()
    val sortBy by viewModel.sortBy.collectAsState()

    // 局部搜索输入状态（用于输入框显示）
    var localSearchQuery by remember { mutableStateOf("") }

    // 同步搜索状态
    LaunchedEffect(searchQuery) {
        localSearchQuery = searchQuery
    }

    // 缓存计算结果
    val isListEmpty by remember {
        derivedStateOf { actors.isEmpty() }
    }

    val hasFilters by remember {
        derivedStateOf {
            searchQuery.isNotEmpty() || selectedCountry != null || selectedCategory != null
        }
    }

    // 底部筛选面板状态
    val sheetState = rememberModalBottomSheetState()
    var showFilterSheet by remember { mutableStateOf(false) }

    // 临时筛选状态（用于底部面板）
    var tempCountry by remember { mutableStateOf<String?>(null) }
    var tempCategory by remember { mutableStateOf<String?>(null) }
    var tempSortBy by remember { mutableStateOf<ActorSortBy>(ActorSortBy.RATE_DESC) }

    // 顶部栏高度和偏移状态
    var topBarHeightPx by remember { mutableFloatStateOf(0f) }
    var topBarOffsetHeightPx by remember { mutableFloatStateOf(0f) }
    val topBarHeightDp = with(LocalDensity.current) { topBarHeightPx.toDp() }

    // 底部导航栏控制
    val bottomBarVisible = LocalBottomBarVisible.current
    val nestedScrollConnection = remember(topBarHeightPx) {
        object : NestedScrollConnection {
            override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset {
                // 底部栏逻辑
                if (available.y < -5f) {
                    bottomBarVisible.value = false
                } else if (available.y > 5f) {
                    bottomBarVisible.value = true
                }

                // 顶部栏逻辑
                val delta = available.y
                val newOffset = topBarOffsetHeightPx + delta
                if (topBarHeightPx > 0) {
                    topBarOffsetHeightPx = newOffset.coerceIn(-topBarHeightPx, 0f)
                }

                return Offset.Zero
            }
        }
    }

    Scaffold(
        modifier = modifier
            .fillMaxSize()
            .nestedScroll(nestedScrollConnection),
        containerColor = MaterialTheme.colorScheme.surface
    ) { paddingValues ->
        Box( // Changed from Column to Box
            modifier = Modifier
                .fillMaxSize()
                .padding(bottom = paddingValues.calculateBottomPadding()) // Only bottom padding
        ) {
            // Instagram 风格搜索和筛选栏
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 搜索栏
                SearchBar(
                    query = localSearchQuery,
                    onQueryChanged = { localSearchQuery = it },
                    onSearch = { viewModel.searchActors(it) },
                    placeholder = "搜索演员...",
                    modifier = Modifier.weight(1f)
                )

                // Instagram 风格筛选按钮
                InstagramFilterButton(
                    hasActiveFilters = selectedCountry != null || selectedCategory != null,
                    onClick = { showFilterSheet = true })
            }

            // 当前筛选标签显示
            AnimatedVisibility(
                visible = hasFilters,
                enter = fadeIn() + slideInVertically(),
                exit = fadeOut() + slideOutVertically()
            ) {
                ActiveFiltersRow(
                    selectedCountry = selectedCountry,
                    selectedCategory = selectedCategory,
                    sortBy = sortBy,
                    onClearAll = {
                        viewModel.filterByCountry(null)
                        viewModel.filterByCategory(null)
                        viewModel.sortBy(ActorSortBy.RATE_DESC)
                    },
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
                )
            }

            // 内容区域 (Layer 1)
            Box(
                modifier = Modifier.fillMaxSize()
            ) {
                when {
                    uiState.isLoading -> {
                        LoadingIndicator()
                    }

                    isListEmpty -> {
                        Box(modifier = Modifier.padding(top = topBarHeightDp)) { // Added padding
                            EmptyState(
                                message = if (hasFilters) {
                                    "没有找到符合条件的演员"
                                } else {
                                    "暂无演员数据\n点击下方按钮添加演员"
                                }
                            )
                        }
                    }

                    else -> {
                        LazyColumn(
                            state = viewModel.gridState, contentPadding = PaddingValues(
                                top = topBarHeightDp + 8.dp,
                                start = 16.dp,
                                end = 16.dp,
                                bottom = 88.dp
                            ), // Added top padding
                            verticalArrangement = Arrangement.spacedBy(2.dp)
                        ) {
                            items(
                                items = actors,
                                key = { it.id },
                                contentType = { "actor" }) { actor ->
                                val onClickCallback = remember(actor.id) { { onActorClick(actor) } }

                                ActorCard(
                                    actor = actor,
                                    onClick = onClickCallback,
                                    modifier = Modifier.fillMaxWidth()
                                )

                                // 分隔线 - Instagram 风格极细分隔线
                                if (actor != actors.last()) {
                                    HorizontalDivider(
                                        thickness = 0.5.dp,
                                        color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.3f)
                                    )
                                }
                            }

                            // 底部间距，避开 FAB
                            item {
                                Spacer(modifier = Modifier.height(100.dp))
                            }
                        }
                    }
                }

                // Instagram 风格添加按钮 - 渐变色
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(16.dp)
                        .padding(bottom = 56.dp)
                ) {
                    FloatingActionButton(
                        onClick = onAddActor,
                        containerColor = Color.Transparent,
                        modifier = Modifier.background(instagramGradient, CircleShape)
                    ) {
                        Icon(
                            Icons.Default.Add, contentDescription = "添加演员", tint = Color.White
                        )
                    }
                }

                // Instagram 风格搜索和筛选栏 (Layer 2 - Header)
                Column(modifier = Modifier
                    .fillMaxWidth()
                    .onGloballyPositioned { coordinates ->
                        topBarHeightPx = coordinates.size.height.toFloat()
                    }
                    .offset { IntOffset(x = 0, y = topBarOffsetHeightPx.roundToInt()) }
                    .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.98f))
                    .statusBarsPadding()
                    .zIndex(1f)) {
                    // Instagram 风格搜索和筛选栏
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 12.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // 搜索栏
                        SearchBar(
                            query = localSearchQuery,
                            onQueryChanged = { localSearchQuery = it },
                            onSearch = { viewModel.searchActors(it) },
                            placeholder = "搜索演员...",
                            modifier = Modifier.weight(1f)
                        )

                        // Instagram 风格筛选按钮
                        InstagramFilterButton(
                            hasActiveFilters = selectedCountry != null || selectedCategory != null,
                            onClick = { showFilterSheet = true })
                    }

                    // 当前筛选标签显示
                    AnimatedVisibility(
                        visible = hasFilters,
                        enter = fadeIn() + slideInVertically(),
                        exit = fadeOut() + slideOutVertically()
                    ) {
                        ActiveFiltersRow(
                            selectedCountry = selectedCountry,
                            selectedCategory = selectedCategory,
                            sortBy = sortBy,
                            onClearAll = {
                                viewModel.filterByCountry(null)
                                viewModel.filterByCategory(null)
                                viewModel.sortBy(ActorSortBy.RATE_DESC)
                            },
                            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
                        )
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

        // Instagram 风格底部筛选面板
        if (showFilterSheet) {
            // 初始化临时状态为当前筛选值
            LaunchedEffect(Unit) {
                tempCountry = selectedCountry
                tempCategory = selectedCategory
                tempSortBy = sortBy
            }

            ModalBottomSheet(
                onDismissRequest = { showFilterSheet = false },
                sheetState = sheetState,
                containerColor = MaterialTheme.colorScheme.surface,
                dragHandle = {
                    // Instagram 风格拖拽条
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Box(
                            modifier = Modifier
                                .width(40.dp)
                                .height(4.dp)
                                .background(
                                    MaterialTheme.colorScheme.outlineVariant,
                                    RoundedCornerShape(2.dp)
                                )
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                    }
                }) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 20.dp)
                        .padding(bottom = 32.dp), verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // 标题栏
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "筛选", style = MaterialTheme.typography.titleLarge.copy(
                                fontWeight = FontWeight.Bold, fontSize = 18.sp
                            )
                        )

                        TextButton(
                            onClick = {
                                tempCountry = null
                                tempCategory = null
                                tempSortBy = ActorSortBy.RATE_DESC
                            }) {
                            Text(
                                text = "重置",
                                color = InstagramGradientMiddle,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }

                    HorizontalDivider(
                        thickness = 0.5.dp,
                        color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f)
                    )

                    // 筛选选项
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        // 国家筛选
                        FilterSection(
                            title = "国家/地区",
                            options = emptyList(), // 暂时使用空列表
                            selectedOption = tempCountry,
                            onOptionSelected = { tempCountry = it })

                        // 类别筛选
                        FilterSection(
                            title = "类别",
                            options = emptyList(), // 暂时使用空列表
                            selectedOption = tempCategory,
                            onOptionSelected = { tempCategory = it })

                        // 排序选项
                        FilterSection(
                            title = "排序方式",
                            options = ActorSortBy.entries.map { it.displayName },
                            selectedOption = tempSortBy.displayName,
                            onOptionSelected = { selected ->
                                tempSortBy = ActorSortBy.entries.find { it.displayName == selected }
                                    ?: ActorSortBy.RATE_DESC
                            })
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    // 应用按钮 - Instagram 渐变色
                    Button(
                        onClick = {
                            viewModel.filterByCountry(tempCountry)
                            viewModel.filterByCategory(tempCategory)
                            viewModel.sortBy(tempSortBy)
                            showFilterSheet = false
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = InstagramGradientMiddle
                        )
                    ) {
                        Text(
                            text = "应用筛选", fontWeight = FontWeight.SemiBold, fontSize = 15.sp
                        )
                    }
                }
            }
        }
    }
}

/**
 * 筛选选项区域组件
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun FilterSection(
        title: String,
        options: List<String>,
        selectedOption: String?,
        onOptionSelected: (String?) -> Unit,
        modifier: Modifier = Modifier
    ) {
        val instagramGradient = Brush.linearGradient(
            colors = listOf(
                InstagramGradientStart, InstagramGradientMiddle, InstagramGradientEnd
            )
        )

        Column(
            modifier = modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = title, style = MaterialTheme.typography.bodyMedium.copy(
                    fontWeight = FontWeight.Medium, fontSize = 14.sp
                ), color = TextSecondary
            )

            FlowRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                options.forEach { option ->
                    val isSelected = option == selectedOption

                    FilterChip(
                        selected = isSelected, onClick = {
                        onOptionSelected(if (isSelected) null else option)
                    }, label = {
                        Text(
                            text = option,
                            fontSize = 13.sp,
                            fontWeight = if (isSelected) FontWeight.Medium else FontWeight.Normal
                        )
                    }, colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = InstagramGradientMiddle.copy(alpha = 0.15f),
                        selectedLabelColor = InstagramGradientMiddle,
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                        labelColor = MaterialTheme.colorScheme.onSurface
                    ), border = FilterChipDefaults.filterChipBorder(
                        borderColor = Color.Transparent,
                        selectedBorderColor = InstagramGradientMiddle.copy(alpha = 0.5f),
                        enabled = true,
                        selected = isSelected
                    ), shape = RoundedCornerShape(20.dp)
                    )
                }
            }
        }
    }

    /**
     * 当前激活筛选标签行
     */
    @OptIn(ExperimentalLayoutApi::class)
    @Composable
    private fun ActiveFiltersRow(
        selectedCountry: String?,
        selectedCategory: String?,
        sortBy: ActorSortBy,
        onClearAll: () -> Unit,
        modifier: Modifier = Modifier
    ) {
        FlowRow(
            modifier = modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            selectedCountry?.let {
                ActiveFilterChip(label = it, onRemove = { /* 单独移除逻辑 */ })
            }
            selectedCategory?.let {
                ActiveFilterChip(label = it, onRemove = { /* 单独移除逻辑 */ })
            }
            if (sortBy != ActorSortBy.RATE_DESC) {
                ActiveFilterChip(label = sortBy.displayName, onRemove = { /* 单独移除逻辑 */ })
            }

            // 清除全部按钮
            TextButton(
                onClick = onClearAll,
                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 0.dp),
                modifier = Modifier.height(28.dp)
            ) {
                Text(
                    text = "清除全部",
                    fontSize = 12.sp,
                    color = InstagramGradientMiddle,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }

    /**
     * 激活的筛选标签
     */
    @Composable
    private fun ActiveFilterChip(
        label: String, onRemove: () -> Unit, modifier: Modifier = Modifier
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
