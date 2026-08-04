package com.example.myapplication.ui.screens.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.myapplication.data.service.ThumbnailDisplayMode
import com.example.myapplication.ui.viewmodel.SettingsViewModel
import com.example.myapplication.ui.viewmodel.SyncUiState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(viewModel: SettingsViewModel) {
    val syncState by viewModel.syncState.collectAsState()
    val hasCursor by viewModel.hasCursor.collectAsState()
    val thumbnailMode by viewModel.thumbnailMode.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("设置") })
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 显示设置卡片
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "缩略图布局",
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = "马赛克：按图片比例动态拼接（Telegram 风格）。\n网格：等分正方形，按数量显示 2 或 3 列。",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    val modes = listOf(
                        ThumbnailDisplayMode.MOSAIC to "马赛克",
                        ThumbnailDisplayMode.GRID to "网格"
                    )
                    SingleChoiceSegmentedButtonRow(modifier = Modifier.fillMaxWidth()) {
                        modes.forEachIndexed { index, (mode, label) ->
                            SegmentedButton(
                                selected = thumbnailMode == mode,
                                onClick = { viewModel.setThumbnailMode(mode) },
                                shape = SegmentedButtonDefaults.itemShape(index, modes.size)
                            ) {
                                Text(label)
                            }
                        }
                    }
                }
            }

            // 同步卡片
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "数据同步",
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = if (hasCursor)
                            "增量同步：拉取上次之后的变更。首次或游标失效时请先「初始化」。"
                        else "尚未初始化，请先执行「初始化全量同步」拉取全量数据（合集、消息、媒体、标签）。",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )

                    val isSyncing = syncState is SyncUiState.Syncing

                    // 增量同步（日常，主按钮）
                    Button(
                        onClick = { viewModel.syncIncremental() },
                        enabled = !isSyncing && hasCursor,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (isSyncing) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp,
                                color = MaterialTheme.colorScheme.onPrimary
                            )
                            Spacer(Modifier.width(8.dp))
                            Text("同步中...")
                        } else {
                            Text("增量同步")
                        }
                    }

                    // 初始化全量同步（次按钮）
                    OutlinedButton(
                        onClick = { viewModel.syncFull() },
                        enabled = !isSyncing,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(if (hasCursor) "重新初始化（全量同步）" else "初始化全量同步")
                    }

                    // 结果展示
                    when (val state = syncState) {
                        is SyncUiState.Success -> {
                            Card(
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.primaryContainer
                                )
                            ) {
                                Text(
                                    text = state.summary,
                                    style = MaterialTheme.typography.bodySmall,
                                    modifier = Modifier.padding(12.dp)
                                )
                            }
                        }

                        is SyncUiState.Error -> {
                            Card(
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.errorContainer
                                )
                            ) {
                                Text(
                                    text = state.message,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onErrorContainer,
                                    modifier = Modifier.padding(12.dp)
                                )
                            }
                        }

                        else -> {}
                    }
                }
            }
        }
    }
}
