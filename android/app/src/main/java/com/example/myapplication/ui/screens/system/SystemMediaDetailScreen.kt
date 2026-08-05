package com.example.myapplication.ui.screens.system

import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import coil.compose.AsyncImage
import com.example.myapplication.data.model.SystemMedia
import com.example.myapplication.data.repository.SystemMediaRepository
import com.example.myapplication.ui.components.TelegramVideoPlayer
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SystemMediaDetailScreen(
    mediaUri: String,
    mediaList: List<SystemMedia>,
    navController: NavController,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val repository = remember(context) { SystemMediaRepository(context.applicationContext) }
    val initialIndex = mediaList.indexOfFirst { it.uri.toString() == mediaUri }
    var fallbackMedia by remember(mediaUri) { mutableStateOf<SystemMedia?>(null) }
    var isLoading by remember(mediaUri) { mutableStateOf(initialIndex < 0) }
    var loadError by remember(mediaUri) { mutableStateOf(false) }

    LaunchedEffect(mediaUri, initialIndex) {
        if (initialIndex < 0) {
            fallbackMedia = try {
                withContext(Dispatchers.IO) {
                    repository.getMediaByUri(Uri.parse(mediaUri))
                }
            } catch (_: SecurityException) {
                loadError = true
                null
            }
            isLoading = false
        }
    }

    if (isLoading) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        return
    }

    val pagerItems = if (initialIndex >= 0) mediaList else listOfNotNull(fallbackMedia)
    if (pagerItems.isEmpty()) {
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

    val pagerState = rememberPagerState(initialPage = initialIndex.coerceAtLeast(0)) {
        pagerItems.size
    }
    val currentMedia = pagerItems[pagerState.currentPage]

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(currentMedia.displayName, maxLines = 1, overflow = TextOverflow.Ellipsis)
                },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = modifier.fillMaxSize().padding(paddingValues)
        ) {
            HorizontalPager(
                state = pagerState,
                key = { pagerItems[it].stableKey },
                modifier = Modifier.fillMaxWidth().weight(1f).background(Color.Black),
                beyondViewportPageCount = 0
            ) { page ->
                val pageMedia = pagerItems[page]
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    if (pageMedia.isVideo) {
                        TelegramVideoPlayer(
                            videoPath = pageMedia.uri.toString(),
                            autoPlay = page == pagerState.currentPage,
                            modifier = Modifier.fillMaxSize()
                        )
                    } else {
                        AsyncImage(
                            model = pageMedia.uri,
                            contentDescription = pageMedia.displayName,
                            modifier = Modifier.fillMaxSize(),
                            contentScale = ContentScale.Fit
                        )
                    }
                }
            }

            Column(
                modifier = Modifier.fillMaxWidth().padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text(currentMedia.displayName, style = MaterialTheme.typography.titleMedium)
                Text(
                    listOfNotNull(
                        if (currentMedia.isVideo) "视频" else "图片",
                        currentMedia.resolution,
                        currentMedia.getFormattedDuration(),
                        currentMedia.getFormattedSize()
                    ).joinToString(" · "),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
