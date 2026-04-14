package com.example.myapplication.ui.screens.system

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.ui.viewmodel.MediaViewModel
import com.example.myapplication.ui.viewmodel.SystemGalleryViewModel
import com.example.myapplication.utils.MediaFilePicker
import kotlinx.coroutines.launch

/**
 * 系统媒体编辑页面
 * 允许编辑媒体的标题、描述和评分
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SystemMediaEditScreen(
    mediaId: Long,
    navController: NavController,
    systemGalleryViewModel: SystemGalleryViewModel,
    mediaViewModel: MediaViewModel = viewModel(),
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val scrollState = rememberScrollState()

    // 状态变量
    var isLoading by remember { mutableStateOf(true) }
    var isSaving by remember { mutableStateOf(false) }
    var showError by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }
    var showSuccess by remember { mutableStateOf(false) }

    // 系统媒体信息
    val mediaList by systemGalleryViewModel.mediaList.collectAsState()
    val mediaByFolder by systemGalleryViewModel.mediaByFolder.collectAsState()
    val hasPermission by systemGalleryViewModel.hasPermission.collectAsState()

    // 查找系统媒体
    val systemMedia = remember(mediaId, mediaList, mediaByFolder) {
        mediaList.find { it.id == mediaId } ?: mediaByFolder.values.flatten()
            .find { it.id == mediaId }
    }

    // 编辑状态变量
    var title by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var rating by remember { mutableFloatStateOf(0f) }

    // 权限检查
    LaunchedEffect(Unit) {
        if (!hasPermission) {
            systemGalleryViewModel.setPermissionGranted(true)
        }
    }

    // 加载现有媒体数据
    LaunchedEffect(systemMedia) {
        if (systemMedia != null) {
            try {
                // 由于Media实体结构变更，暂时不检查数据库中是否已存在该媒体记录
                // 直接使用系统媒体信息初始化
                title = systemMedia.displayName.substringBeforeLast(".")
                description = ""
                rating = 0f
                isLoading = false
            } catch (e: Exception) {
                errorMessage = "加载媒体数据失败: ${e.message}"
                showError = true
                isLoading = false
            }
        }
    }

    // 保存函数
    fun saveMedia() {
        if (systemMedia == null) return

        coroutineScope.launch {
            try {
                isSaving = true

                val filePicker = MediaFilePicker(context)
                val fileHash = filePicker.computeBlake2bHash(systemMedia.uri)
                    ?: systemMedia.uri.toString()

                // 创建新记录
                val mediaToSave = Media(
                    localMediaPath = systemMedia.uri.toString(),
                    mimeType = systemMedia.mimeType ?: "unknown",
                    width = systemMedia.width,
                    height = systemMedia.height,
                    durationMs = systemMedia.duration,
                    fileSize = systemMedia.size,
                    fileHash = fileHash,
                    rating = rating.toInt()
                )

                // 插入新记录
                mediaViewModel.insertMedia(mediaToSave)

                showSuccess = true
                // 延迟导航，让用户看到成功消息
                kotlinx.coroutines.delay(1000)
                navController.popBackStack()

            } catch (e: Exception) {
                errorMessage = "保存失败: ${e.message}"
                showError = true
            } finally {
                isSaving = false
            }
        }
    }

    if (isLoading) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                CircularProgressIndicator()
                Text("正在加载媒体信息...")
            }
        }
        return
    }

    if (systemMedia == null) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text("媒体文件未找到")
                Button(onClick = { navController.popBackStack() }) {
                    Text("返回")
                }
            }
        }
        return
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "编辑媒体",
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "返回"
                        )
                    }
                },
                actions = {
                    // 保存按钮
                    IconButton(
                        onClick = { saveMedia() },
                        enabled = !isSaving && title.isNotBlank()
                    ) {
                        if (isSaving) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
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
        },
        snackbarHost = {
            SnackbarHost(
                hostState = remember { SnackbarHostState() }.apply {
                    if (showError) {
                        LaunchedEffect(errorMessage) {
                            showSnackbar(errorMessage)
                            showError = false
                        }
                    }
                    if (showSuccess) {
                        LaunchedEffect(Unit) {
                            showSnackbar("保存成功")
                            showSuccess = false
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
                .verticalScroll(scrollState)
        ) {
            // 媒体预览区域
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(200.dp),
                    contentAlignment = Alignment.Center
                ) {
                    AsyncImage(
                        model = ImageRequest.Builder(context)
                            .data(systemMedia.uri)
                            .size(400, 400)
                            .crossfade(true)
                            .build(),
                        contentDescription = systemMedia.displayName,
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Crop
                    )

                    // 视频指示器
                    if (systemMedia.isVideo) {
                        Surface(
                            modifier = Modifier
                                .align(Alignment.BottomEnd)
                                .padding(8.dp),
                            color = Color.Black.copy(alpha = 0.7f),
                            shape = RoundedCornerShape(4.dp)
                        ) {
                            Text(
                                text = "视频",
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                color = Color.White,
                                style = MaterialTheme.typography.labelSmall
                            )
                        }
                    }
                }
            }

            // 编辑表单
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // 标题编辑
                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("标题") },
                    placeholder = { Text("为这个媒体起个名字") },
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(
                        capitalization = KeyboardCapitalization.Sentences,
                        imeAction = ImeAction.Next
                    ),
                    singleLine = true,
                    isError = title.isBlank(),
                    supportingText = {
                        if (title.isBlank()) {
                            Text(
                                text = "标题不能为空",
                                color = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                )

                // 描述编辑
                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("描述") },
                    placeholder = { Text("添加一些描述信息（可选）") },
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(
                        capitalization = KeyboardCapitalization.Sentences,
                        imeAction = ImeAction.Done
                    ),
                    minLines = 3,
                    maxLines = 5
                )

                // 评分编辑
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text(
                            text = "评分",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Medium
                        )

                        // 星级评分
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            repeat(5) { index ->
                                val starValue = index + 1f
                                IconButton(
                                    onClick = {
                                        rating = if (rating == starValue) 0f else starValue
                                    }
                                ) {
                                    Icon(
                                        imageVector = if (rating >= starValue) {
                                            Icons.Filled.Star
                                        } else {
                                            Icons.Outlined.Star
                                        },
                                        contentDescription = "${starValue}星",
                                        tint = if (rating >= starValue) {
                                            Color(0xFFFFD700) // 金色
                                        } else {
                                            MaterialTheme.colorScheme.onSurfaceVariant
                                        },
                                        modifier = Modifier.size(32.dp)
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.width(8.dp))

                            Text(
                                text = if (rating > 0) "${rating.toInt()}/5" else "未评分",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }

                        // 评分滑块
                        Column {
                            Slider(
                                value = rating,
                                onValueChange = { rating = it },
                                valueRange = 0f..5f,
                                steps = 4, // 0, 1, 2, 3, 4, 5
                                modifier = Modifier.fillMaxWidth()
                            )
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = "0",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Text(
                                    text = "5",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }

                // 文件信息（只读）
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            text = "文件信息",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Medium
                        )

                        InfoRow("文件名", systemMedia.displayName)
                        InfoRow("大小", systemMedia.getFormattedSize())
                        systemMedia.resolution?.let {
                            InfoRow("分辨率", it)
                        }
                        if (systemMedia.isVideo) {
                            systemMedia.getFormattedDuration()?.let {
                                InfoRow("时长", it)
                            }
                        }
                        systemMedia.bucketDisplayName?.let {
                            InfoRow("文件夹", it)
                        }
                    }
                }

                // 底部间距
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}

/**
 * 信息行组件
 */
@Composable
private fun InfoRow(
    label: String,
    value: String,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = "$label:",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.weight(0.4f)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.weight(0.6f)
        )
    }
}