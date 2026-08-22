package com.example.myapplication.ui.screens.system

import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.example.myapplication.data.model.SystemMedia
import com.example.myapplication.data.repository.SystemMediaRepository
import com.example.myapplication.ui.components.SharedMediaViewer
import com.example.myapplication.ui.components.TagSelectorDialog
import com.example.myapplication.ui.model.toViewerMediaItem
import com.example.myapplication.ui.viewmodel.MediaViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable
fun SystemMediaDetailScreen(
    mediaUri: String,
    mediaList: List<SystemMedia>,
    mediaViewModel: MediaViewModel,
    navController: NavController,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val repository = remember(context) { SystemMediaRepository(context.applicationContext) }
    val metadataItems by mediaViewModel.allMediaWithMetadata.collectAsState()
    val metadataRows by mediaViewModel.metadata.collectAsState()
    val tagLinks by mediaViewModel.tagLinks.collectAsState()
    val allTags by mediaViewModel.allTags.collectAsState()
    val initialIndex = mediaList.indexOfFirst { it.uri.toString() == mediaUri }
    var fallbackMedia by remember(mediaUri) { mutableStateOf<SystemMedia?>(null) }
    var isLoading by remember(mediaUri) { mutableStateOf(initialIndex < 0) }
    var loadError by remember(mediaUri) { mutableStateOf(false) }
    var tagEditorKey by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(mediaUri, initialIndex) {
        if (initialIndex < 0) {
            fallbackMedia = try {
                withContext(Dispatchers.IO) { repository.getMediaByUri(Uri.parse(mediaUri)) }
            } catch (_: SecurityException) {
                loadError = true
                null
            }
            isLoading = false
        }
    }

    if (isLoading) {
        Box(
            Modifier.fillMaxSize().background(Color.Black),
            contentAlignment = Alignment.Center
        ) { CircularProgressIndicator(color = Color.White) }
        return
    }

    val systemItems = if (initialIndex >= 0) mediaList else listOfNotNull(fallbackMedia)
    if (systemItems.isEmpty()) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(if (loadError) "没有权限访问该媒体" else "媒体文件未找到")
                Button(onClick = { navController.popBackStack() }) { Text("返回") }
            }
        }
        return
    }

    val metadataByKey = remember(systemItems, metadataItems, metadataRows, tagLinks, allTags) {
        val existingByKey = metadataItems.associateBy { it.media.stableKey }
        val metadataRowsByKey = metadataRows.associateBy { it.stableKey }
        val tagsById = allTags.associateBy { it.id }
        val tagIdsByKey = tagLinks.groupBy { it.systemMediaKey }
        systemItems.associate { media ->
            media.stableKey to (existingByKey[media.stableKey]
                ?: com.example.myapplication.ui.model.SystemMediaWithMetadata(
                    media = media,
                    starred = metadataRowsByKey[media.stableKey]?.starred == true,
                    tags = tagIdsByKey[media.stableKey].orEmpty()
                        .mapNotNull { tagsById[it.tagId] }
                ))
        }
    }
    val pagerState = rememberPagerState(initialPage = initialIndex.coerceAtLeast(0)) {
        systemItems.size
    }
    val stripListState = rememberLazyListState()
    val viewerItems = remember(systemItems, metadataByKey) {
        systemItems.map { media ->
            media.toViewerMediaItem(metadataByKey[media.stableKey]?.starred ?: false)
        }
    }

    SharedMediaViewer(
        items = viewerItems,
        pagerState = pagerState,
        stripListState = stripListState,
        totalCount = systemItems.size,
        onClose = { navController.popBackStack() },
        modifier = modifier,
        onToggleStar = { page ->
            metadataByKey[systemItems[page].stableKey]?.let(mediaViewModel::toggleStarred)
                ?: mediaViewModel.toggleStarred(
                    com.example.myapplication.ui.model.SystemMediaWithMetadata(systemItems[page])
                )
        },
        onEditTags = { page -> tagEditorKey = systemItems[page].stableKey }
    )

    val editingItem = tagEditorKey?.let(metadataByKey::get)
    TagSelectorDialog(
        show = tagEditorKey != null,
        allTags = allTags,
        selectedTags = editingItem?.tags.orEmpty(),
        onTagSelectionChanged = { tags ->
            val media = systemItems.find { it.stableKey == tagEditorKey }
            if (media != null) {
                mediaViewModel.setTags(
                    editingItem ?: com.example.myapplication.ui.model.SystemMediaWithMetadata(media),
                    tags
                )
            }
        },
        onDismiss = { tagEditorKey = null },
        title = "编辑媒体标签"
    )
}
