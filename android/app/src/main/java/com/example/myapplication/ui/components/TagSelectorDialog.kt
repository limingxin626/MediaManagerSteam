package com.example.myapplication.ui.components

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.myapplication.data.database.entities.Tag

/**
 * 标签选择对话框
 * 可复用的标签选择器组件
 *
 * @param show 是否显示对话框
 * @param allTags 所有可选标签列表
 * @param selectedTags 当前已选择的标签列表
 * @param onTagSelectionChanged 标签选择改变时的回调，传入新的选中标签列表
 * @param onDismiss 关闭对话框的回调
 * @param title 对话框标题，默认为"选择标签"
 * @param confirmText 确认按钮文本，默认为"确定"
 * @param cancelText 取消按钮文本，默认为"取消"
 */
@Composable
fun TagSelectorDialog(
    show: Boolean,
    allTags: List<Tag>,
    selectedTags: List<Tag>,
    onTagSelectionChanged: (List<Tag>) -> Unit,
    onDismiss: () -> Unit,
    title: String = "选择标签",
    confirmText: String = "确定",
    cancelText: String = "取消"
) {
    if (show) {
        // 使用本地状态来管理临时选择，避免外部状态的频繁更新
        var tempSelectedTags by remember(selectedTags) {
            mutableStateOf(selectedTags)
        }

        AlertDialog(
            onDismissRequest = onDismiss,
            title = {
                Text(title)
            },
            text = {
                if (allTags.isEmpty()) {
                    // 空状态提示
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(100.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "暂无可选标签",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                } else {
                    // 标签列表
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(300.dp) // 限制高度，避免对话框过大
                    ) {
                        items(allTags) { tag ->
                            TagSelectionItem(
                                tag = tag,
                                isSelected = tempSelectedTags.any { it.id == tag.id },
                                onSelectionChanged = { isSelected ->
                                    tempSelectedTags = if (isSelected) {
                                        tempSelectedTags + tag
                                    } else {
                                        tempSelectedTags.filter { it.id != tag.id }
                                    }
                                }
                            )
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        onTagSelectionChanged(tempSelectedTags)
                        onDismiss()
                    }
                ) {
                    Text(confirmText)
                }
            },
            dismissButton = {
                TextButton(
                    onClick = onDismiss
                ) {
                    Text(cancelText)
                }
            }
        )
    }
}

/**
 * 单个标签选择项组件
 */
@Composable
private fun TagSelectionItem(
    tag: Tag,
    isSelected: Boolean,
    onSelectionChanged: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Checkbox(
            checked = isSelected,
            onCheckedChange = onSelectionChanged
        )
        Spacer(modifier = Modifier.width(8.dp))
        Column {
            Text(
                text = tag.name,
                style = MaterialTheme.typography.bodyMedium
            )
            tag.category?.let { category ->
                Text(
                    text = category,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}