package com.example.myapplication.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.myapplication.data.model.SystemMedia

/**
 * 文件夹组件
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FolderSection(
    folderName: String,
    mediaList: List<SystemMedia>,
    isExpanded: Boolean,
    isSelectionMode: Boolean,
    selectedMedia: Set<SystemMedia>,
    onFolderClick: (String) -> Unit,
    onMediaClick: (SystemMedia) -> Unit,
    onMediaLongClick: (SystemMedia) -> Unit = {},
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxWidth()
    ) {
        // 文件夹标题栏
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onFolderClick(folderName) },
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
            ),
            shape = RoundedCornerShape(8.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.PlayArrow,
                        contentDescription = "文件夹",
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(20.dp)
                    )

                    Column {
                        Text(
                            text = folderName,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Medium
                        )
                        Text(
                            text = "${mediaList.size} 个文件",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                Icon(
                    imageVector = if (isExpanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                    contentDescription = if (isExpanded) "收起" else "展开",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        // 展开的媒体网格
        AnimatedVisibility(
            visible = isExpanded,
            enter = expandVertically(),
            exit = shrinkVertically()
        ) {
            LazyVerticalGrid(
                columns = GridCells.Fixed(3),
                contentPadding = PaddingValues(top = 8.dp, bottom = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(4.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
                modifier = Modifier.heightIn(max = 600.dp) // 限制最大高度
            ) {
                items(
                    items = mediaList,
                    key = { it.id }
                ) { media ->
                    SystemMediaCard(
                        media = media,
                        isSelected = selectedMedia.contains(media),
                        isSelectionMode = isSelectionMode,
                        onMediaClick = onMediaClick,
                        onMediaLongClick = onMediaLongClick
                    )
                }
            }
        }
    }
}

/**
 * 文件夹预览组件（显示文件夹封面）
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FolderPreviewCard(
    folderName: String,
    mediaList: List<SystemMedia>,
    onFolderClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onFolderClick(folderName) },
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column {
            // 显示前4个媒体作为预览
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1f)
            ) {
                when {
                    mediaList.isEmpty() -> {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.PlayArrow,
                                contentDescription = "空文件夹",
                                modifier = Modifier.size(48.dp),
                                tint = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    mediaList.size == 1 -> {
                        // 单个媒体，全屏显示
                        SystemMediaCard(
                            media = mediaList[0],
                            onMediaClick = { onFolderClick(folderName) },
                            modifier = Modifier.fillMaxSize()
                        )
                    }

                    else -> {
                        // 多个媒体，2x2网格预览
                        Column {
                            Row(modifier = Modifier.weight(1f)) {
                                SystemMediaCard(
                                    media = mediaList[0],
                                    onMediaClick = { onFolderClick(folderName) },
                                    modifier = Modifier.weight(1f)
                                )
                                if (mediaList.size > 1) {
                                    SystemMediaCard(
                                        media = mediaList[1],
                                        onMediaClick = { onFolderClick(folderName) },
                                        modifier = Modifier.weight(1f)
                                    )
                                }
                            }
                            if (mediaList.size > 2) {
                                Row(modifier = Modifier.weight(1f)) {
                                    SystemMediaCard(
                                        media = mediaList[2],
                                        onMediaClick = { onFolderClick(folderName) },
                                        modifier = Modifier.weight(1f)
                                    )
                                    if (mediaList.size > 3) {
                                        Box(modifier = Modifier.weight(1f)) {
                                            SystemMediaCard(
                                                media = mediaList[3],
                                                onMediaClick = { onFolderClick(folderName) },
                                                modifier = Modifier.fillMaxSize()
                                            )
                                            // 如果还有更多，显示数量
                                            if (mediaList.size > 4) {
                                                Box(
                                                    modifier = Modifier
                                                        .fillMaxSize()
                                                        .padding(4.dp),
                                                    contentAlignment = Alignment.BottomEnd
                                                ) {
                                                    Surface(
                                                        color = MaterialTheme.colorScheme.surface.copy(
                                                            alpha = 0.8f
                                                        ),
                                                        shape = RoundedCornerShape(4.dp)
                                                    ) {
                                                        Text(
                                                            text = "+${mediaList.size - 4}",
                                                            modifier = Modifier.padding(4.dp),
                                                            style = MaterialTheme.typography.labelSmall
                                                        )
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // 文件夹信息
            Column(
                modifier = Modifier.padding(12.dp)
            ) {
                Text(
                    text = folderName,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Medium
                )
                Text(
                    text = "${mediaList.size} 个文件",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}