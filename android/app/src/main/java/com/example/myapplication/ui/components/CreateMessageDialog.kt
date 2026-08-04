package com.example.myapplication.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Collection

/**
 * 创建消息对话框
 */
@Composable
fun CreateMessageDialog(
    onDismiss: () -> Unit,
    onConfirm: (Long?, String) -> Unit,
    databaseManager: DatabaseManager? = null,
    defaultCollectionId: Long? = null
) {
    var text by remember { mutableStateOf("") }
    var selectedCollectionId by remember { mutableStateOf(defaultCollectionId) }
    var collections by remember { mutableStateOf<List<Collection>>(emptyList()) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = "创建消息",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold
                )
            )
        },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // 消息文本
                OutlinedTextField(
                    value = text,
                    onValueChange = { text = it },
                    label = { Text("消息内容") },
                    placeholder = { Text("请输入消息内容") },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 4
                )

                // 合集选择
                if (collections.isNotEmpty()) {
                    Column {
                        Text(
                            text = "选择合集",
                            style = MaterialTheme.typography.bodyMedium.copy(
                                fontWeight = FontWeight.Medium
                            ),
                            modifier = Modifier.padding(bottom = 8.dp)
                        )
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            collections.forEach { collection ->
                                FilterChip(
                                    selected = selectedCollectionId == collection.id,
                                    onClick = { selectedCollectionId = collection.id },
                                    label = { Text(collection.name) },
                                    modifier = Modifier
                                )
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    onConfirm(selectedCollectionId, text)
                },
                enabled = text.isNotBlank()
            ) {
                Text(
                    text = "创建",
                    fontWeight = FontWeight.Medium
                )
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        }
    )
}
