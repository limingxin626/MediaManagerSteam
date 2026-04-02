package com.example.myapplication.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.outlined.List
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

import com.example.myapplication.ui.theme.InstagramGradientEnd
import com.example.myapplication.ui.theme.InstagramGradientMiddle
import com.example.myapplication.ui.theme.InstagramGradientStart
import com.example.myapplication.ui.theme.TextSecondary

/**
 * 通用枚举下拉选择组件
 * @param T 枚举类型
 * @param value 当前选中的值（编辑模式下不能为null，筛选模式下可以为null）
 * @param onValueChange 值改变回调
 * @param label 标签文本或占位符文本
 * @param options 所有可选项列表
 * @param getDisplayName 获取枚举显示名称的函数
 * @param modifier 修饰符
 * @param allowNull 是否允许null值（筛选模式）
 * @param allOptionText "全部"选项的显示文本
 * @param isFilter 是否为筛选模式（影响UI样式）
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun <T> EnumDropdownField(
    value: T?,
    onValueChange: (T?) -> Unit,
    label: String,
    options: List<T>,
    getDisplayName: (T) -> String,
    modifier: Modifier = Modifier,
    allowNull: Boolean = false,
    allOptionText: String = "全部",
    isFilter: Boolean = false
) {
    var expanded by remember { mutableStateOf(false) }

    // 计算显示文本
    val displayText = if (value != null) {
        getDisplayName(value)
    } else {
        if (allowNull) allOptionText else label
    }

    ExposedDropdownMenuBox(
        expanded = expanded, onExpandedChange = { expanded = it }) {
        OutlinedTextField(
            value = displayText,
            onValueChange = {},
            readOnly = true,
            label = { Text(label) },
            trailingIcon = {
                ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
            },
            modifier = modifier
                .fillMaxWidth()
                .menuAnchor(),
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = MaterialTheme.colorScheme.onSurface,
                unfocusedTextColor = MaterialTheme.colorScheme.onSurface,
                focusedLabelColor = MaterialTheme.colorScheme.primary,
                unfocusedLabelColor = MaterialTheme.colorScheme.onSurfaceVariant
            ),
            textStyle = MaterialTheme.typography.bodyMedium,
            singleLine = true
        )

        ExposedDropdownMenu(
            expanded = expanded, onDismissRequest = { expanded = false }) {
            // 如果允许null值，添加"全部"选项
            if (allowNull) {
                DropdownMenuItem(
                    text = { Text(allOptionText) }, onClick = {
                        onValueChange(null)
                        expanded = false
                    }, contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp)
                )
            }

            // 枚举选项
            options.forEach { option ->
                DropdownMenuItem(
                    text = { Text(getDisplayName(option)) }, onClick = {
                        onValueChange(option)
                        expanded = false
                    }, contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp)
                )
            }
        }
    }
}

/**
 * Instagram 风格搜索栏组件
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchBar(
    query: String,
    onQueryChanged: (String) -> Unit,
    onSearch: (String) -> Unit = {},
    placeholder: String = "搜索...",
    modifier: Modifier = Modifier
) {
    val interactionSource = remember { MutableInteractionSource() }
    val textStyle = MaterialTheme.typography.bodyMedium.copy(
        fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurface
    )

    BasicTextField(
        value = query,
        onValueChange = onQueryChanged,
        modifier = modifier
            .fillMaxWidth()
            .height(44.dp),
        singleLine = true,
        textStyle = textStyle,
        cursorBrush = SolidColor(InstagramGradientMiddle),
        keyboardOptions = KeyboardOptions(
            imeAction = ImeAction.Search
        ),
        keyboardActions = KeyboardActions(
            onSearch = { onSearch(query) }),
        interactionSource = interactionSource,
        decorationBox = { innerTextField ->
            TextFieldDefaults.DecorationBox(
                value = query,
                innerTextField = innerTextField,
                enabled = true,
                singleLine = true,
                visualTransformation = VisualTransformation.None,
                interactionSource = interactionSource,
                placeholder = {
                    Text(
                        placeholder, style = MaterialTheme.typography.bodyMedium.copy(
                            color = TextSecondary, fontSize = 14.sp
                        )
                    )
                },
                leadingIcon = {
                    Icon(
                        Icons.Default.Search,
                        contentDescription = "搜索",
                        modifier = Modifier.size(20.dp),
                        tint = TextSecondary
                    )
                },
                trailingIcon = {
                    AnimatedVisibility(
                        visible = query.isNotEmpty(), enter = fadeIn(), exit = fadeOut()
                    ) {
                        IconButton(
                            onClick = {
                                onQueryChanged("")
                                onSearch("")
                            }, modifier = Modifier.size(32.dp)
                        ) {
                            Icon(
                                Icons.Default.Clear,
                                contentDescription = "清空",
                                modifier = Modifier.size(18.dp),
                                tint = TextSecondary
                            )
                        }
                    }
                },
                shape = RoundedCornerShape(12.dp),
                colors = TextFieldDefaults.colors(
                    focusedTextColor = MaterialTheme.colorScheme.onSurface,
                    unfocusedTextColor = MaterialTheme.colorScheme.onSurface,
                    focusedPlaceholderColor = TextSecondary,
                    unfocusedPlaceholderColor = TextSecondary,
                    focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                    unfocusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                    focusedIndicatorColor = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent,
                    cursorColor = InstagramGradientMiddle
                ),
                contentPadding = PaddingValues(horizontal = 4.dp, vertical = 8.dp),
                container = {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .clip(RoundedCornerShape(12.dp))
                            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                    )
                })
        })
}


/**
 * Instagram 风格加载指示器
 */
@Composable
fun LoadingIndicator(
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(32.dp), strokeWidth = 2.dp, color = InstagramGradientMiddle
        )
    }
}

/**
 * Instagram 风格空状态显示
 */
@Composable
fun EmptyState(
    message: String, modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Instagram 风格的空图标
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.surfaceVariant),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Search,
                    contentDescription = null,
                    modifier = Modifier.size(32.dp),
                    tint = TextSecondary
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = message, style = MaterialTheme.typography.bodyMedium.copy(
                    fontSize = 14.sp, fontWeight = FontWeight.Normal
                ), color = TextSecondary
            )
        }
    }
}

/**
 * Instagram 风格筛选按钮
 */
@Composable
fun InstagramFilterButton(
    hasActiveFilters: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier
) {
    val gradientBrush = Brush.linearGradient(
        colors = listOf(
            InstagramGradientStart, InstagramGradientMiddle, InstagramGradientEnd
        )
    )

    Surface(
        modifier = modifier.height(44.dp),
        shape = RoundedCornerShape(12.dp),
        color = if (hasActiveFilters) Color.Transparent
        else MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
        onClick = onClick
    ) {
        Box(
            modifier = if (hasActiveFilters) {
                Modifier
                    .background(gradientBrush, RoundedCornerShape(12.dp))
                    .padding(horizontal = 16.dp)
            } else {
                Modifier.padding(horizontal = 16.dp)
            }, contentAlignment = Alignment.Center
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.List,
                    contentDescription = "筛选",
                    modifier = Modifier.size(18.dp),
                    tint = if (hasActiveFilters) Color.White else TextSecondary
                )
                Text(
                    text = "筛选", style = MaterialTheme.typography.bodyMedium.copy(
                        fontSize = 14.sp, fontWeight = FontWeight.Medium
                    ), color = if (hasActiveFilters) Color.White else TextSecondary
                )
            }
        }
    }
}