package com.example.myapplication.ui.screens.message

import android.net.Uri
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import coil.compose.AsyncImage
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.ui.components.OptimizedThumbnail
import com.example.myapplication.utils.MediaFileInfo
import com.example.myapplication.utils.MediaFilePicker
import com.example.myapplication.utils.ThumbnailGenerator
import com.example.myapplication.utils.rememberMultipleMediaFilePicker
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MessageEditScreen(
    messageId: Long,
    databaseManager: DatabaseManager,
    navController: NavController,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    var isLoading by remember { mutableStateOf(true) }
    var isSaving by remember { mutableStateOf(false) }

    // Form state
    var text by remember { mutableStateOf("") }
    var starred by remember { mutableStateOf(false) }
    var existingMedia by remember { mutableStateOf<List<Media>>(emptyList()) }
    var removedMediaIds by remember { mutableStateOf<Set<Long>>(emptySet()) }
    val newMedia = remember { mutableStateListOf<MediaFileInfo>() }

    val mediaPickerLauncher = rememberMultipleMediaFilePicker(maxItems = 10) { mediaFiles ->
        newMedia.addAll(mediaFiles)
    }

    // Load existing data
    LaunchedEffect(messageId) {
        val details = databaseManager.messageRepository.getMessageWithDetails(messageId)
        if (details != null) {
            text = details.message.text ?: ""
            starred = details.message.starred
            existingMedia = details.mediaList
        }
        isLoading = false
    }

    // Save logic
    val save: () -> Unit = {
        coroutineScope.launch {
            try {
                isSaving = true
                val messageRepo = databaseManager.messageRepository
                val original = messageRepo.getMessageById(messageId) ?: return@launch

                // 1. Update message text and starred
                messageRepo.updateMessage(original.copy(text = text.ifBlank { null }, starred = starred))

                // 2. Rebuild media associations
                messageRepo.deleteMessageMediaByMessageId(messageId)
                val keptMedia = existingMedia.filter { it.id !in removedMediaIds }
                keptMedia.forEachIndexed { index, media ->
                    messageRepo.addMediaToMessage(messageId, media.id, position = index)
                }

                // 3. Insert new media
                val filePicker = MediaFilePicker(context)
                val thumbnailGenerator = ThumbnailGenerator(context)
                var position = keptMedia.size
                for (mediaFileInfo in newMedia) {
                    val localPath = filePicker.copyFileToAppStorage(mediaFileInfo.uri, mediaFileInfo.fileName)
                    val fileHash = filePicker.computeBlake2bHash(mediaFileInfo.uri) ?: mediaFileInfo.uri.toString()
                    val resolution = filePicker.getMediaResolution(mediaFileInfo.uri)
                    val width = resolution?.split("x")?.getOrNull(0)?.toIntOrNull()
                    val height = resolution?.split("x")?.getOrNull(1)?.toIntOrNull()
                    val isVideo = mediaFileInfo.mimeType?.startsWith("video/") == true
                    val durationMs = if (isVideo) filePicker.getVideoDuration(mediaFileInfo.uri)?.let { it * 1000 } else null
                    val thumbnailPath = localPath?.let { thumbnailGenerator.generateThumbnail(it, isVideo) }

                    val media = Media(
                        fileHash = fileHash,
                        localMediaPath = localPath,
                        localThumbnailPath = thumbnailPath,
                        mimeType = mediaFileInfo.mimeType,
                        fileSize = mediaFileInfo.size,
                        width = width,
                        height = height,
                        durationMs = durationMs
                    )
                    val mediaId = databaseManager.mediaRepository.insertMedia(media)
                    messageRepo.addMediaToMessage(messageId, mediaId, position = position)
                    position++
                }

                // 4. Re-parse tags
                messageRepo.deleteMessageTagsByMessageId(messageId)
                messageRepo.parseAndAttachTags(text, messageId, databaseManager.tagRepository)

                navController.navigateUp()
            } catch (_: Exception) {
            } finally {
                isSaving = false
            }
        }
    }

    if (isLoading) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
    } else {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("编辑消息") },
                    navigationIcon = {
                        IconButton(onClick = { navController.navigateUp() }) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                        }
                    },
                    actions = {
                        IconButton(
                            onClick = save,
                            enabled = !isSaving
                        ) {
                            if (isSaving) {
                                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                            } else {
                                Icon(Icons.Default.Check, contentDescription = "保存")
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
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Text input
                Text("消息内容", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Medium)
                Card(modifier = Modifier.fillMaxWidth()) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 120.dp)
                            .padding(16.dp)
                    ) {
                        if (text.isEmpty()) {
                            Text(
                                "输入消息文本...",
                                style = MaterialTheme.typography.bodyLarge.copy(
                                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f)
                                )
                            )
                        }
                        BasicTextField(
                            value = text,
                            onValueChange = { text = it },
                            modifier = Modifier.fillMaxWidth(),
                            textStyle = MaterialTheme.typography.bodyLarge.copy(
                                color = MaterialTheme.colorScheme.onSurface
                            ),
                            cursorBrush = SolidColor(MaterialTheme.colorScheme.primary)
                        )
                    }
                }

                // Starred toggle
                Card(modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 8.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("收藏", style = MaterialTheme.typography.bodyLarge)
                        IconButton(onClick = { starred = !starred }) {
                            Icon(
                                if (starred) Icons.Filled.Star else Icons.Outlined.Star,
                                contentDescription = if (starred) "取消收藏" else "收藏",
                                tint = if (starred) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }

                // Existing media
                val keptMedia = existingMedia.filter { it.id !in removedMediaIds }
                if (keptMedia.isNotEmpty() || newMedia.isNotEmpty()) {
                    Text(
                        "媒体附件 (${keptMedia.size + newMedia.size})",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Medium
                    )
                }

                if (keptMedia.isNotEmpty()) {
                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        itemsIndexed(keptMedia, key = { _, media -> media.id }) { _, media ->
                            ExistingMediaItem(
                                media = media,
                                onRemove = { removedMediaIds = removedMediaIds + media.id }
                            )
                        }
                    }
                }

                // New media preview
                if (newMedia.isNotEmpty()) {
                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        itemsIndexed(newMedia) { index, mediaFile ->
                            NewMediaItem(
                                mediaFileInfo = mediaFile,
                                onRemove = { newMedia.removeAt(index) }
                            )
                        }
                    }
                }

                // Add media button
                OutlinedButton(
                    onClick = {
                        mediaPickerLauncher.launch(
                            PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageAndVideo)
                        )
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("添加媒体")
                }
            }
        }
    }
}

@Composable
private fun ExistingMediaItem(
    media: Media,
    onRemove: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .size(80.dp)
            .clip(RoundedCornerShape(8.dp))
    ) {
        OptimizedThumbnail(
            thumbnailPath = media.thumbnailPath ?: media.filePath,
            modifier = Modifier.fillMaxSize()
        )
        IconButton(
            onClick = onRemove,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .size(24.dp)
                .padding(2.dp)
        ) {
            Surface(
                shape = CircleShape,
                color = Color.Black.copy(alpha = 0.6f),
                modifier = Modifier.size(20.dp)
            ) {
                Icon(
                    Icons.Default.Close,
                    contentDescription = "移除",
                    tint = Color.White,
                    modifier = Modifier.padding(2.dp)
                )
            }
        }
    }
}

@Composable
private fun NewMediaItem(
    mediaFileInfo: MediaFileInfo,
    onRemove: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .size(80.dp)
            .clip(RoundedCornerShape(8.dp))
    ) {
        AsyncImage(
            model = mediaFileInfo.uri,
            contentDescription = mediaFileInfo.fileName,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize()
        )
        IconButton(
            onClick = onRemove,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .size(24.dp)
                .padding(2.dp)
        ) {
            Surface(
                shape = CircleShape,
                color = Color.Black.copy(alpha = 0.6f),
                modifier = Modifier.size(20.dp)
            ) {
                Icon(
                    Icons.Default.Close,
                    contentDescription = "移除",
                    tint = Color.White,
                    modifier = Modifier.padding(2.dp)
                )
            }
        }
    }
}
