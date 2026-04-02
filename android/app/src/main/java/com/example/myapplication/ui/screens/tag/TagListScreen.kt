package com.example.myapplication.ui.screens.tag

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.input.nestedscroll.nestedScroll
import com.example.myapplication.LocalBottomBarVisible
import com.example.myapplication.data.database.entities.Tag
import com.example.myapplication.ui.components.*
import com.example.myapplication.ui.viewmodel.TagViewModel

/**
 * 标签列表页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TagListScreen(
    viewModel: TagViewModel,
    onTagClick: (Tag) -> Unit = {},
    onAddTag: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    // 优化状态收集，减少不必要的重组
    val uiState by viewModel.uiState.collectAsState()
    val tags by viewModel.tags.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    val selectedCategory by viewModel.selectedCategory.collectAsState()
    val categories by viewModel.categories.collectAsState()

    // 缓存计算结果
    val isListEmpty by remember {
        derivedStateOf { tags.isEmpty() }
    }

    val hasFilters by remember {
        derivedStateOf { searchQuery.isNotEmpty() || selectedCategory != null }
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
        modifier = modifier.fillMaxSize().nestedScroll(nestedScrollConnection)
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // 搜索和筛选栏
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 搜索栏
                SearchBar(
                    query = searchQuery,
                    onQueryChanged = viewModel::searchTags,
                    placeholder = "搜索标签名称...",
                    modifier = Modifier.weight(2f)
                )
                
                // 分类筛选
                EnumDropdownField(
                    value = selectedCategory,
                    onValueChange = viewModel::filterByCategory,
                    label = "分类",
                    options = categories,
                    getDisplayName = { it },
                    modifier = Modifier.width(100.dp),
                    allowNull = true,
                    allOptionText = "全部",
                    isFilter = true
                )
            }

            // 内容区域
            Box(modifier = Modifier.weight(1f)) {
                when {
                    uiState.isLoading -> {
                        LoadingIndicator()
                    }

                    isListEmpty -> {
                        EmptyState(
                            message = if (hasFilters) {
                                "没有找到符合条件的标签"
                            } else {
                                "暂无标签数据\n点击右下角按钮添加标签"
                            }
                        )
                    }

                    else -> {
                        LazyVerticalGrid(
                            columns = GridCells.Fixed(2), // 使用固定列数提高性能
                            state = viewModel.gridState,
                            contentPadding = PaddingValues(top = 8.dp, start = 8.dp, end = 8.dp, bottom = 88.dp),
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            items(
                                items = tags,
                                key = { it.id },
                                contentType = { "tag" } // 添加内容类型提示
                            ) { tag ->
                                // 缓存回调函数避免重复创建
                                val onClickCallback = remember(tag.id) { { onTagClick(tag) } }

                                TagCard(
                                    tag = tag,
                                    onClick = onClickCallback
                                )
                            }
                        }
                    }
                }

                // 添加按钮
                FloatingActionButton(
                    onClick = onAddTag,
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(16.dp)
                        .padding(bottom = 56.dp) // 额外的底部间距，避开导航栏
                ) {
                    Icon(Icons.Default.Add, contentDescription = "添加标签")
                }
            }
        }

        // 错误消息处理
        uiState.error?.let { error ->
            LaunchedEffect(error) {
                // 这里可以显示 Snackbar 或其他错误提示
                // 为了简化，暂时只是清除错误
                viewModel.clearError()
            }
        }

        // 成功消息处理
        uiState.message?.let { message ->
            LaunchedEffect(message) {
                // 这里可以显示 Snackbar
                viewModel.clearMessage()
            }
        }
    }
}
