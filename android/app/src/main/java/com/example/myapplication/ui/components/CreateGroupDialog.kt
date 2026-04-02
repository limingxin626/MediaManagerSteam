package com.example.myapplication.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * 创建分组对话框组件
 * 可复用的组件，用于创建新的分组
 */
@Composable
fun CreateGroupDialog(
    onDismiss: () -> Unit,
    onConfirm: (actorId: Long, name: String, description: String, score: Float) -> Unit,
    defaultActorId: Long = 1L,
    modifier: Modifier = Modifier
) {
    var actorId by remember { mutableStateOf(defaultActorId.toString()) }
    var name by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var score by remember { mutableStateOf("0.0") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("创建新分组") },
        text = {
            Column(
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                OutlinedTextField(
                    value = actorId,
                    onValueChange = { actorId = it },
                    label = { Text("演员ID") },
                    placeholder = { Text("请输入演员ID") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("分组标题") },
                    placeholder = { Text("请输入分组标题") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                
                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("分组描述") },
                    placeholder = { Text("请输入分组描述") },
                    maxLines = 3,
                    modifier = Modifier.fillMaxWidth()
                )
                
                OutlinedTextField(
                    value = score,
                    onValueChange = { score = it },
                    label = { Text("评分 (0-5)") },
                    placeholder = { Text("0.0") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    val actorIdLong = actorId.toLongOrNull()
                    val scoreFloat = score.toFloatOrNull() ?: 0.0f
                    
                    if (actorIdLong != null && name.isNotBlank()) {
                        onConfirm(actorIdLong, name, description, scoreFloat)
                    }
                },
                enabled = actorId.toLongOrNull() != null && name.isNotBlank()
            ) {
                Text("创建")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        },
        modifier = modifier
    )
}