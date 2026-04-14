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
import com.example.myapplication.data.database.entities.Actor

/**
 * 创建消息对话框
 */
@Composable
fun CreateMessageDialog(
    onDismiss: () -> Unit,
    onConfirm: (Long?, String) -> Unit,
    databaseManager: DatabaseManager? = null,
    defaultActorId: Long? = null
) {
    var text by remember { mutableStateOf("") }
    var selectedActorId by remember { mutableStateOf(defaultActorId) }
    var actors by remember { mutableStateOf<List<Actor>>(emptyList()) }

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

                // 演员选择
                if (actors.isNotEmpty()) {
                    Column {
                        Text(
                            text = "选择演员",
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
                            actors.forEach { actor ->
                                FilterChip(
                                    selected = selectedActorId == actor.id,
                                    onClick = { selectedActorId = actor.id },
                                    label = { Text(actor.name) },
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
                    onConfirm(selectedActorId, text)
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
