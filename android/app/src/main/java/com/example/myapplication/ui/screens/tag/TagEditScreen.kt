package com.example.myapplication.ui.screens.tag

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Tag
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.navigation.Routes
import com.example.myapplication.ui.components.MediaCard
import com.example.myapplication.ui.components.EmptyState
import kotlinx.coroutines.launch

/**
 * 标签编辑页面
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TagEditScreen(
    tagId: Long? = null, // null表示新增，非null表示编辑
    databaseManager: DatabaseManager,
    navController: NavController,
    modifier: Modifier = Modifier
) {
    var tag by remember { mutableStateOf<Tag?>(null) }
    var isLoading by remember { mutableStateOf(tagId != null) }
    val coroutineScope = rememberCoroutineScope()
    
    // 表单状态
    var tagName by remember { mutableStateOf("") }
    var tagCategory by remember { mutableStateOf("") }
    
    // 验证状态
    var nameError by remember { mutableStateOf<String?>(null) }
    var isFormValid by remember { mutableStateOf(false) }
    var isSaving by remember { mutableStateOf(false) }
    
    // 媒体列表状态
    var mediaList by remember { mutableStateOf<List<Media>>(emptyList()) }
    
    // 删除对话框状态
    var showDeleteDialog by remember { mutableStateOf(false) }
    
    val focusManager = LocalFocusManager.current

    // 加载现有标签数据（编辑模式）
    LaunchedEffect(tagId) {
        if (tagId != null) {
            coroutineScope.launch {
                tag = databaseManager.tagRepository.getTagById(tagId)
                tag?.let { loadedTag ->
                    tagName = loadedTag.name
                    tagCategory = loadedTag.category ?: ""
                }
                isLoading = false
            }
        }
    }
    
    // 加载标签关联的媒体列表（仅编辑模式）
    LaunchedEffect(tagId) {
        if (tagId != null) {
            databaseManager.tagRepository.getMediaForTag(tagId).collect { media ->
                mediaList = media
            }
        }
    }

    // 验证表单
    LaunchedEffect(tagName) {
        nameError = when {
            tagName.isBlank() -> "标签名称不能为空"
            tagName.length < 2 -> "标签名称至少2个字符"
            tagName.length > 50 -> "标签名称不能超过50个字符"
            else -> null
        }
        
        isFormValid = nameError == null && tagName.isNotBlank()
    }

    // 保存函数
    val saveTag = remember {
        {
            if (isFormValid) {
                coroutineScope.launch {
                    try {
                        isSaving = true
                        
                        if (tagId == null) {
                            // 新增标签
                            val newTag = Tag(
                                name = tagName.trim(),
                                category = tagCategory.trim().takeIf { it.isNotEmpty() }
                            )
                            databaseManager.tagRepository.createOrGetTag(newTag.name, newTag.category)
                        } else {
                            // 更新标签
                            val updatedTag = tag!!.copy(
                                name = tagName.trim(),
                                category = tagCategory.trim().takeIf { it.isNotEmpty() }
                            )
                            databaseManager.tagRepository.updateTag(updatedTag)
                        }
                        
                        navController.navigateUp()
                    } catch (e: Exception) {
                        // 处理错误，这里可以显示错误消息
                    } finally {
                        isSaving = false
                    }
                }
            }
        }
    }
    
    // 删除函数
    val deleteTag = remember {
        {
            coroutineScope.launch {
                try {
                    if (tagId != null && tag != null) {
                        databaseManager.tagRepository.deleteTag(tag!!)
                        navController.navigateUp()
                    }
                } catch (e: Exception) {
                    // 处理错误
                }
            }
        }
    }

    if (isLoading) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            CircularProgressIndicator()
        }
    } else {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text(if (tagId == null) "添加标签" else "编辑标签") },
                    navigationIcon = {
                        IconButton(onClick = { navController.navigateUp() }) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "返回"
                            )
                        }
                    },
                    actions = {
                        // 删除按钮（仅编辑模式显示）
                        if (tagId != null) {
                            IconButton(
                                onClick = { showDeleteDialog = true }
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Delete,
                                    contentDescription = "删除标签",
                                    tint = MaterialTheme.colorScheme.error
                                )
                            }
                        }
                        
                        // 保存按钮
                        IconButton(
                            onClick = saveTag,
                            enabled = isFormValid && !isSaving
                        ) {
                            if (isSaving) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(20.dp),
                                    strokeWidth = 2.dp
                                )
                            } else {
                                Icon(
                                    imageVector = Icons.Default.Check,
                                    contentDescription = "保存"
                                )
                            }
                        }
                    }
                )
            }
        ) { paddingValues ->
            Column(
                modifier = modifier
                    .fillMaxSize()
                    .padding(paddingValues)
            ) {
                // 上方表单部分
                Column(
                    modifier = Modifier
                        .padding(horizontal = 16.dp)
                        .padding(top = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // 编辑信息标题
                    Text(
                        text = "标签信息",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Medium,
                        modifier = Modifier.padding(vertical = 8.dp)
                    )
                    
                    // 表单内容
                    Card(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            // 标签名称
                            OutlinedTextField(
                                value = tagName,
                                onValueChange = { tagName = it },
                                label = { Text("标签名称 *") },
                                isError = nameError != null,
                                supportingText = nameError?.let { { Text(it) } },
                                keyboardOptions = KeyboardOptions(
                                    imeAction = ImeAction.Next
                                ),
                                keyboardActions = KeyboardActions(
                                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                                ),
                                modifier = Modifier.fillMaxWidth()
                            )
                            
                            // 分类
                            OutlinedTextField(
                                value = tagCategory,
                                onValueChange = { tagCategory = it },
                                label = { Text("分类") },
                                placeholder = { Text("如：类型、风格、主题等") },
                                keyboardOptions = KeyboardOptions(
                                    imeAction = ImeAction.Done
                                ),
                                keyboardActions = KeyboardActions(
                                    onDone = { focusManager.clearFocus() }
                                ),
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }
                
                // 媒体列表部分（仅编辑模式显示）
                if (tagId != null) {
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Text(
                        text = "关联的媒体 (${mediaList.size})",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Medium,
                        modifier = Modifier.padding(horizontal = 16.dp)
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    // 媒体网格列表
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .weight(1f)
                    ) {
                        if (mediaList.isEmpty()) {
                            EmptyState(
                                message = "此标签暂未关联任何媒体",
                                modifier = Modifier.padding(16.dp)
                            )
                        } else {
                            LazyVerticalGrid(
                                columns = GridCells.Fixed(2),
                                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                                horizontalArrangement = Arrangement.spacedBy(4.dp),
                                verticalArrangement = Arrangement.spacedBy(4.dp)
                            ) {
                                items(
                                    items = mediaList,
                                    key = { it.id }
                                ) { media ->
                                    MediaCard(
                                        media = media,
                                        onClick = { 
                                            navController.navigate(Routes.mediaDetail(media.id))
                                        }
                                    )
                                }
                            }
                        }
                    }
                } else {
                    // 新增模式下的底部空间
                    Spacer(modifier = Modifier.height(16.dp))
                }
            }
        }
        
        // 删除确认对话框
        if (showDeleteDialog) {
            AlertDialog(
                onDismissRequest = { showDeleteDialog = false },
                title = { Text("确认删除") },
                text = {
                    Text("确定要删除标签 \"$tagName\" 吗？\n\n删除后，此标签与媒体的关联关系也将被移除。此操作不可撤销。")
                },
                confirmButton = {
                    TextButton(
                        onClick = {
                            showDeleteDialog = false
                            deleteTag()
                        }
                    ) {
                        Text("删除", color = MaterialTheme.colorScheme.error)
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showDeleteDialog = false }) {
                        Text("取消")
                    }
                }
            )
        }
    }
}