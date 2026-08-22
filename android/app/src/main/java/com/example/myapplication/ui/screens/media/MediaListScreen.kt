package com.example.myapplication.ui.screens.media

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.grid.rememberLazyGridState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.example.myapplication.LocalBottomBarVisible
import com.example.myapplication.data.model.SystemMedia
import com.example.myapplication.ui.model.SystemMediaWithMetadata
import com.example.myapplication.ui.model.orderedSelectedSystemMedia
import com.example.myapplication.ui.model.updateSystemMediaSelection
import com.example.myapplication.ui.components.SystemMediaCard
import com.example.myapplication.ui.viewmodel.MediaViewModel

@Composable
fun MediaListScreen(
    viewModel: MediaViewModel,
    onMediaClick: (SystemMedia) -> Unit = {},
    onCreateMessage: (List<SystemMedia>, () -> Unit) -> Unit = { _, done -> done() },
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val uiState by viewModel.uiState.collectAsState()
    val mediaList by viewModel.mediaList.collectAsState()
    val allTags by viewModel.allTags.collectAsState()
    val starredOnly by viewModel.starredOnly.collectAsState()
    val selectedTagId by viewModel.selectedTagId.collectAsState()
    val gridState = rememberLazyGridState()
    var showTagMenu by remember { mutableStateOf(false) }
    var selectionMode by remember { mutableStateOf(false) }
    var selectedKeys by remember { mutableStateOf(emptySet<String>()) }
    var isSubmitting by remember { mutableStateOf(false) }
    val currentSelectedKeys by rememberUpdatedState(selectedKeys)
    val currentSelectionMode by rememberUpdatedState(selectionMode)

    LaunchedEffect(mediaList) {
        selectedKeys = selectedKeys.intersect(mediaList.mapTo(mutableSetOf()) { it.media.stableKey })
    }

    fun setSelected(key: String, selected: Boolean) {
        selectedKeys = updateSystemMediaSelection(selectedKeys, key, selected)
    }

    fun cancelSelection() {
        selectionMode = false
        selectedKeys = emptySet()
        isSubmitting = false
    }

    fun currentPermissions(): Pair<Boolean, Boolean> {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
            val granted = ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_EXTERNAL_STORAGE
            ) == PackageManager.PERMISSION_GRANTED
            return granted to granted
        }
        val images = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_MEDIA_IMAGES
        ) == PackageManager.PERMISSION_GRANTED
        val videos = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.READ_MEDIA_VIDEO
        ) == PackageManager.PERMISSION_GRANTED
        val selected = Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE &&
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED
            ) == PackageManager.PERMISSION_GRANTED
        return (images || selected) to (videos || selected)
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        val (images, videos) = currentPermissions()
        viewModel.updatePermissions(images, videos)
    }

    val requestPermissions = {
        permissionLauncher.launch(
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                arrayOf(
                    Manifest.permission.READ_MEDIA_IMAGES,
                    Manifest.permission.READ_MEDIA_VIDEO,
                    Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED
                )
            } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                arrayOf(Manifest.permission.READ_MEDIA_IMAGES, Manifest.permission.READ_MEDIA_VIDEO)
            } else {
                arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE)
            }
        )
    }

    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                val (images, videos) = currentPermissions()
                viewModel.updatePermissions(images, videos)
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    val bottomBarVisible = LocalBottomBarVisible.current
    val nestedScrollConnection = remember {
        object : NestedScrollConnection {
            override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset {
                if (available.y < -5f) bottomBarVisible.value = false
                else if (available.y > 5f) bottomBarVisible.value = true
                return Offset.Zero
            }
        }
    }

    Scaffold(
        modifier = modifier.fillMaxSize().nestedScroll(nestedScrollConnection),
        containerColor = MaterialTheme.colorScheme.surface
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(bottom = paddingValues.calculateBottomPadding())
        ) {
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "媒体",
                    style = MaterialTheme.typography.titleLarge,
                    modifier = Modifier.weight(1f)
                )
                IconButton(onClick = viewModel::toggleStarredFilter) {
                    Icon(
                        Icons.Default.Star,
                        contentDescription = "收藏筛选",
                        tint = if (starredOnly) Color(0xFFFFD700)
                        else MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Box {
                    IconButton(onClick = { showTagMenu = true }) {
                        Icon(
                            Icons.Default.MoreVert,
                            contentDescription = "标签筛选",
                            tint = if (selectedTagId != null) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    DropdownMenu(
                        expanded = showTagMenu,
                        onDismissRequest = { showTagMenu = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text("全部标签") },
                            onClick = {
                                viewModel.selectTagFilter(null)
                                showTagMenu = false
                            }
                        )
                        allTags.forEach { tag ->
                            DropdownMenuItem(
                                text = { Text(tag.name) },
                                onClick = {
                                    viewModel.selectTagFilter(tag.id)
                                    showTagMenu = false
                                }
                            )
                        }
                    }
                }
            }

            Box(modifier = Modifier.fillMaxSize()) {
                when {
                    uiState.permissionDenied -> MediaPageState(
                        message = "需要照片或视频访问权限",
                        actionLabel = "授权访问",
                        onAction = requestPermissions
                    )

                    uiState.isLoading -> CircularProgressIndicator(Modifier.align(Alignment.Center))

                    uiState.error != null -> MediaPageState(
                        message = uiState.error ?: "加载失败",
                        actionLabel = "重试",
                        onAction = viewModel::refreshMedia
                    )

                    mediaList.isEmpty() -> MediaPageState(message = "没有可访问的系统媒体")

                    else -> Box(Modifier.fillMaxSize()) {
                        LazyVerticalGrid(
                            columns = GridCells.Fixed(3),
                            state = gridState,
                            contentPadding = PaddingValues(
                                start = 2.dp,
                                end = 2.dp,
                                bottom = if (selectionMode) 152.dp else 88.dp
                            ),
                            horizontalArrangement = Arrangement.spacedBy(2.dp),
                            verticalArrangement = Arrangement.spacedBy(2.dp),
                            modifier = Modifier
                                .fillMaxSize()
                                .pointerInput(mediaList) {
                                    var addItems = true
                                    val visited = mutableSetOf<String>()

                                    fun keyAt(position: Offset): String? {
                                        val visible = gridState.layoutInfo.visibleItemsInfo.firstOrNull { info ->
                                            position.x >= info.offset.x &&
                                                position.x < info.offset.x + info.size.width &&
                                                position.y >= info.offset.y &&
                                                position.y < info.offset.y + info.size.height
                                        } ?: return null
                                        return mediaList.getOrNull(visible.index)?.media?.stableKey
                                    }

                                    fun applyAt(position: Offset, first: Boolean = false) {
                                        val key = keyAt(position) ?: return
                                        if (first) addItems = key !in currentSelectedKeys
                                        if (visited.add(key)) setSelected(key, addItems)
                                    }

                                    detectDragGesturesAfterLongPress(
                                        onDragStart = {
                                            if (!currentSelectionMode) selectionMode = true
                                            applyAt(it, first = true)
                                        },
                                        onDragEnd = { visited.clear() },
                                        onDragCancel = { visited.clear() },
                                        onDrag = { change, _ ->
                                            change.consume()
                                            applyAt(change.position)
                                        }
                                    )
                                }
                        ) {
                            items(mediaList, key = { it.media.stableKey }) { item ->
                                val selected = item.media.stableKey in selectedKeys
                                SystemMediaCard(
                                    media = item.media,
                                    starred = item.starred,
                                    isSelectionMode = selectionMode,
                                    isSelected = selected,
                                    onMediaClick = {
                                        if (selectionMode) setSelected(item.media.stableKey, !selected)
                                        else onMediaClick(it)
                                    },
                                    onMediaLongClick = {
                                        if (!selectionMode) {
                                            selectionMode = true
                                            setSelected(item.media.stableKey, true)
                                        }
                                    }
                                )
                            }
                        }

                        if (selectionMode) {
                            Surface(
                                modifier = Modifier
                                    .align(Alignment.BottomCenter)
                                    .padding(horizontal = 16.dp, vertical = 24.dp),
                                shape = MaterialTheme.shapes.large,
                                tonalElevation = 6.dp,
                                shadowElevation = 8.dp
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text("已选择 ${selectedKeys.size} 项")
                                    Spacer(Modifier.width(12.dp))
                                    TextButton(onClick = ::cancelSelection, enabled = !isSubmitting) {
                                        Text("取消")
                                    }
                                    Button(
                                        enabled = selectedKeys.isNotEmpty() && !isSubmitting,
                                        onClick = {
                                            val selected = orderedSelectedSystemMedia(
                                                mediaList,
                                                selectedKeys
                                            )
                                            isSubmitting = true
                                            onCreateMessage(selected, ::cancelSelection)
                                        }
                                    ) {
                                        Text("创建")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun MediaPageState(
    message: String,
    actionLabel: String? = null,
    onAction: () -> Unit = {}
) {
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(message, color = MaterialTheme.colorScheme.onSurfaceVariant)
            if (actionLabel != null) Button(onClick = onAction) { Text(actionLabel) }
        }
    }
}
