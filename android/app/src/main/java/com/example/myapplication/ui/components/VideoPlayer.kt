package com.example.myapplication.ui.components

import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.VectorConverter
import androidx.compose.animation.core.spring
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.changedToUp
import androidx.compose.ui.input.pointer.changedToUpIgnoreConsumed
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.positionChange
import androidx.compose.ui.input.pointer.positionChanged
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.DefaultLoadControl
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.File
import kotlin.math.abs

/**
 * Telegram 风格全屏视频播放器
 * - 进度条永久显示在最底部，可拖动 seek
 * - 点击画面切换播放控件（播放/暂停 + 时间），画面不变灰
 * - 控件显示 3 秒后自动隐藏
 */
@androidx.annotation.OptIn(UnstableApi::class)
@Composable
fun TelegramVideoPlayer(
    videoPath: String,
    autoPlay: Boolean = true,
    modifier: Modifier = Modifier,
    zoomEnabled: Boolean = false,
    onScaleChanged: ((Float) -> Unit)? = null
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    val exoPlayer = remember(videoPath) {
        val loadControl = DefaultLoadControl.Builder()
            .setBufferDurationsMs(
                5_000,   // minBufferMs（默认 50_000）
                15_000,  // maxBufferMs（默认 50_000）
                1_000,   // bufferForPlaybackMs（默认 2_500）
                2_000    // bufferForPlaybackAfterRebufferMs（默认 5_000）
            )
            .build()
        ExoPlayer.Builder(context)
            .setLoadControl(loadControl)
            .build()
            .apply {
                val uri = when {
                    videoPath.startsWith("content://") -> android.net.Uri.parse(videoPath)
                    videoPath.startsWith("http://") || videoPath.startsWith("https://") ->
                        android.net.Uri.parse(videoPath.replace("#", "%23"))

                    else -> android.net.Uri.fromFile(File(videoPath))
                }
                setMediaItem(MediaItem.fromUri(uri))
                prepare()
                playWhenReady = false
            }
    }

    var isPlaying by remember { mutableStateOf(autoPlay) }
    var controlsVisible by remember { mutableStateOf(false) }
    var hideControlsJob by remember { mutableStateOf<Job?>(null) }

    // 进度 & 时长
    var progress by remember { mutableStateOf(0f) }
    var positionMs by remember { mutableStateOf(0L) }
    var durationMs by remember { mutableStateOf(0L) }

    // 拖动 seek 状态
    var isUserSeeking by remember { mutableStateOf(false) }
    var seekPositionMs by remember { mutableStateOf(0L) }

    // 缩放状态（仅 zoomEnabled 时使用）
    val zoomScale = remember { Animatable(1f) }
    val zoomOffset = remember { Animatable(Offset.Zero, Offset.VectorConverter) }
    var containerSize by remember { mutableStateOf(IntSize.Zero) }
    var lastTapTimeMs by remember { mutableStateOf(0L) }
    var lastTapPosition by remember { mutableStateOf(Offset.Zero) }
    var pendingSingleTapJob by remember { mutableStateOf<Job?>(null) }

    LaunchedEffect(zoomScale.value) {
        onScaleChanged?.invoke(zoomScale.value)
    }

    fun calculateBounds(atScale: Float = zoomScale.value): Pair<Offset, Offset> {
        if (containerSize == IntSize.Zero) return Offset.Zero to Offset.Zero
        val maxX = ((atScale - 1f) * containerSize.width / 2f).coerceAtLeast(0f)
        val maxY = ((atScale - 1f) * containerSize.height / 2f).coerceAtLeast(0f)
        return Offset(-maxX, -maxY) to Offset(maxX, maxY)
    }

    fun clampOffset(raw: Offset, atScale: Float = zoomScale.value): Offset {
        val (min, max) = calculateBounds(atScale)
        return Offset(raw.x.coerceIn(min.x, max.x), raw.y.coerceIn(min.y, max.y))
    }

    fun formatMs(ms: Long): String {
        val s = (ms / 1000L).coerceAtLeast(0L)
        val m = (s / 60L).toInt()
        val sec = (s % 60L).toInt()
        return "%d:%02d".format(m, sec)
    }

    fun scheduleHideControls() {
        hideControlsJob?.cancel()
        hideControlsJob = coroutineScope.launch {
            delay(3000)
            controlsVisible = false
        }
    }

    fun toggleControls() {
        if (controlsVisible) {
            hideControlsJob?.cancel()
            controlsVisible = false
        } else {
            controlsVisible = true
            scheduleHideControls()
        }
    }

    fun handleDoubleTap(tapOffset: Offset) {
        coroutineScope.launch {
            if (zoomScale.value > 1.01f) {
                launch { zoomScale.animateTo(1f, spring()) }
                launch { zoomOffset.animateTo(Offset.Zero, spring()) }
            } else {
                val cx = containerSize.width / 2f
                val cy = containerSize.height / 2f
                val targetOffset = Offset(
                    (cx - tapOffset.x) * (2f - 1f),
                    (cy - tapOffset.y) * (2f - 1f)
                )
                val clamped = clampOffset(targetOffset, 2f)
                launch { zoomScale.animateTo(2f, spring()) }
                launch { zoomOffset.animateTo(clamped, spring()) }
            }
        }
    }

    // autoPlay 响应
    LaunchedEffect(exoPlayer, autoPlay) {
        isPlaying = autoPlay
        exoPlayer.playWhenReady = autoPlay
        if (autoPlay) exoPlayer.play() else exoPlayer.pause()
    }

    // 播放器状态监听
    DisposableEffect(exoPlayer) {
        val listener = object : Player.Listener {
            override fun onIsPlayingChanged(playing: Boolean) {
                isPlaying = playing
            }
        }
        exoPlayer.addListener(listener)
        onDispose {
            exoPlayer.removeListener(listener)
            exoPlayer.release()
        }
    }

    // 定时刷新进度
    LaunchedEffect(exoPlayer) {
        while (true) {
            val dur = exoPlayer.duration.coerceAtLeast(1L)
            val pos = exoPlayer.currentPosition
            durationMs = dur
            positionMs = pos
            if (!isUserSeeking) {
                progress = (pos.toFloat() / dur.toFloat()).coerceIn(0f, 1f)
            }
            delay(200)
        }
    }

    Box(
        modifier = modifier
            .onSizeChanged { containerSize = it }
            .then(
                if (zoomEnabled) {
                    // 缩放模式：统一手势处理（双指缩放 + 双击缩放 + 单击控件 + 拖拽平移）
                    Modifier.pointerInput(Unit) {
                        awaitEachGesture {
                            val firstDown = awaitFirstDown(requireUnconsumed = false)
                            var pastTouchSlop = false
                            var didTransform = false

                            while (true) {
                                val event = awaitPointerEvent(PointerEventPass.Main)
                                val activePointers = event.changes.filter { it.pressed }

                                if (activePointers.isEmpty()) {
                                    if (didTransform) {
                                        coroutineScope.launch {
                                            if (zoomScale.value < 1f) {
                                                launch { zoomScale.animateTo(1f, spring()) }
                                                launch {
                                                    zoomOffset.animateTo(
                                                        Offset.Zero,
                                                        spring()
                                                    )
                                                }
                                            } else {
                                                val clamped = clampOffset(zoomOffset.value)
                                                if (clamped != zoomOffset.value) {
                                                    zoomOffset.animateTo(clamped, spring())
                                                }
                                            }
                                        }
                                    } else {
                                        // 无拖拽 → 点击，检测单击/双击
                                        val upChange =
                                            event.changes.firstOrNull { it.changedToUp() }
                                        if (upChange != null) {
                                            val now = System.currentTimeMillis()
                                            val tapPos = upChange.position
                                            val timeSinceLast = now - lastTapTimeMs
                                            val distFromLast =
                                                (tapPos - lastTapPosition).getDistance()

                                            if (timeSinceLast < 300L && distFromLast < viewConfiguration.touchSlop * 3) {
                                                // 双击 → 缩放，取消待执行的单击
                                                pendingSingleTapJob?.cancel()
                                                pendingSingleTapJob = null
                                                handleDoubleTap(tapPos)
                                                lastTapTimeMs = 0L
                                            } else {
                                                // 第一次点击 → 延迟执行单击
                                                lastTapTimeMs = now
                                                lastTapPosition = tapPos
                                                pendingSingleTapJob?.cancel()
                                                pendingSingleTapJob = coroutineScope.launch {
                                                    delay(300L)
                                                    toggleControls()
                                                }
                                            }
                                        }
                                    }
                                    break
                                }

                                if (activePointers.size >= 2) {
                                    // 双指 pinch-to-zoom
                                    val p1 = activePointers[0]
                                    val p2 = activePointers[1]
                                    val prevDist =
                                        (p1.previousPosition - p2.previousPosition).getDistance()
                                    val curDist = (p1.position - p2.position).getDistance()

                                    if (prevDist > 0f && curDist > 0f) {
                                        val zoomFactor = curDist / prevDist
                                        val centroid = (p1.position + p2.position) / 2f
                                        val prevCentroid =
                                            (p1.previousPosition + p2.previousPosition) / 2f
                                        val pan = centroid - prevCentroid

                                        coroutineScope.launch {
                                            val newScale =
                                                (zoomScale.value * zoomFactor).coerceIn(
                                                    0.5f,
                                                    3f
                                                )
                                            zoomScale.snapTo(newScale)
                                            if (newScale > 1f) {
                                                zoomOffset.snapTo(clampOffset(zoomOffset.value + pan))
                                            } else {
                                                zoomOffset.snapTo(Offset.Zero)
                                            }
                                        }
                                        didTransform = true
                                    }
                                    event.changes.forEach { it.consume() }

                                } else if (zoomScale.value > 1.01f) {
                                    // 单指 + 已放大：pan
                                    val pointer = activePointers.first()
                                    val pan = pointer.position - pointer.previousPosition

                                    if (!pastTouchSlop) {
                                        val dist =
                                            (pointer.position - firstDown.position).getDistance()
                                        if (dist > viewConfiguration.touchSlop) {
                                            pastTouchSlop = true
                                        }
                                    }

                                    if (pastTouchSlop && pointer.positionChanged()) {
                                        coroutineScope.launch {
                                            zoomOffset.snapTo(clampOffset(zoomOffset.value + pan))
                                        }
                                        didTransform = true
                                        event.changes.forEach { it.consume() }
                                    }
                                }
                                // scale <= 1 且单指 → 不消费，Pager 处理翻页
                            }
                        }
                    }
                } else {
                    // 非缩放模式：原有的点击切换控件
                    Modifier.pointerInput(Unit) {
                        detectTapGestures { toggleControls() }
                    }
                }
            )
    ) {
        // 视频画面 — useController=false + 移除控制器视图，防止闪现
        AndroidView(
            factory = { ctx ->
                PlayerView(ctx).apply {
                    // 先禁用控制器，再设置 player
                    useController = false
                    controllerAutoShow = false
                    setControllerVisibilityListener(
                        PlayerView.ControllerVisibilityListener { /* no-op */ }
                    )
                    // 隐藏默认控制器的根视图
                    (findViewById<android.view.View>(androidx.media3.ui.R.id.exo_controller)
                            as? android.view.ViewGroup)?.visibility = android.view.View.GONE

                    player = exoPlayer
                    layoutParams = FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                    this.resizeMode = androidx.media3.ui.AspectRatioFrameLayout.RESIZE_MODE_FIT
                    setShowBuffering(PlayerView.SHOW_BUFFERING_NEVER)
                }
            },
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer {
                    scaleX = zoomScale.value
                    scaleY = zoomScale.value
                    translationX = zoomOffset.value.x
                    translationY = zoomOffset.value.y
                }
        )

        // 中间：播放 / 暂停按钮（仅控件可见时显示，无背景变灰）
        AnimatedVisibility(
            visible = controlsVisible,
            enter = fadeIn(),
            exit = fadeOut(),
            modifier = Modifier.align(Alignment.Center)
        ) {
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .background(Color.Black.copy(alpha = 0.45f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                IconButton(
                    onClick = {
                        if (isPlaying) {
                            exoPlayer.pause()
                        } else {
                            exoPlayer.play()
                        }
                        scheduleHideControls()
                    },
                    modifier = Modifier.fillMaxSize()
                ) {
                    if (isPlaying) {
                        // 暂停图标（两条竖线）
                        Canvas(modifier = Modifier.size(36.dp)) {
                            val barW = size.width * 0.22f
                            val barH = size.height * 0.72f
                            val top = (size.height - barH) / 2f
                            val gap = size.width * 0.18f
                            val leftX = (size.width - barW * 2 - gap) / 2f
                            drawRect(
                                color = Color.White,
                                topLeft = androidx.compose.ui.geometry.Offset(leftX, top),
                                size = androidx.compose.ui.geometry.Size(barW, barH)
                            )
                            drawRect(
                                color = Color.White,
                                topLeft = androidx.compose.ui.geometry.Offset(
                                    leftX + barW + gap,
                                    top
                                ),
                                size = androidx.compose.ui.geometry.Size(barW, barH)
                            )
                        }
                    } else {
                        Icon(
                            imageVector = Icons.Default.PlayArrow,
                            contentDescription = "播放",
                            tint = Color.White,
                            modifier = Modifier.size(36.dp)
                        )
                    }
                }
            }
        }

        // 底部区域：永久进度条 + 可见时显示时间
        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
        ) {
            // 时间标签（控件可见时显示）
            AnimatedVisibility(
                visible = controlsVisible,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = formatMs(if (isUserSeeking) seekPositionMs else positionMs),
                        color = Color.White,
                        fontSize = 12.sp
                    )
                    Text(
                        text = formatMs(durationMs),
                        color = Color.White,
                        fontSize = 12.sp
                    )
                }
            }

            // 永久显示的进度条（控件隐藏时：细线；控件显示时：可拖动 Slider）
            if (controlsVisible) {
                Slider(
                    value = if (isUserSeeking) {
                        (seekPositionMs.toFloat() / durationMs.toFloat()).coerceIn(0f, 1f)
                    } else {
                        progress
                    },
                    onValueChange = { v ->
                        if (!isUserSeeking) {
                            isUserSeeking = true
                            hideControlsJob?.cancel()
                        }
                        seekPositionMs = (v * durationMs).toLong()
                        progress = v
                        exoPlayer.seekTo(seekPositionMs)
                    },
                    onValueChangeFinished = {
                        isUserSeeking = false
                        scheduleHideControls()
                    },
                    colors = SliderDefaults.colors(
                        thumbColor = Color.White,
                        activeTrackColor = Color.White,
                        inactiveTrackColor = Color.White.copy(alpha = 0.3f)
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(24.dp)
                )
            } else {
                LinearProgressIndicator(
                    progress = { progress },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(2.dp),
                    color = Color.White,
                    trackColor = Color.White.copy(alpha = 0.25f)
                )
                Spacer(modifier = Modifier.height(11.dp))
            }
        }
    }
}

/**
 * 视频播放器组件
 * @param videoPath 视频文件路径或系统URI
 * @param resizeMode 视频缩放模式：FIT(保持比例), ZOOM(裁剪填充), FIXED_WIDTH(固定宽度)
 */
@androidx.annotation.OptIn(UnstableApi::class)
@Composable
fun VideoPlayer(
    videoPath: String,
    modifier: Modifier = Modifier,
    autoPlay: Boolean = true,
    showControls: Boolean = true,
    resizeMode: Int = androidx.media3.ui.AspectRatioFrameLayout.RESIZE_MODE_FIT
) {
    val context = LocalContext.current

    // 创建 ExoPlayer 实例
    val exoPlayer = remember(videoPath) {
        ExoPlayer.Builder(context)
            .build()
            .apply {
                val uri = when {
                    videoPath.startsWith("content://") -> android.net.Uri.parse(videoPath)
                    videoPath.startsWith("http://") || videoPath.startsWith("https://") ->
                        android.net.Uri.parse(videoPath.replace(" ", "%20"))

                    else -> android.net.Uri.fromFile(File(videoPath))
                }
                val mediaItem = MediaItem.fromUri(uri)
                setMediaItem(mediaItem)
                prepare()
                playWhenReady = false
            }
    }

    // 响应 autoPlay 的变化（Pager 预加载页面会复用 Composable，但不应自动播放）
    LaunchedEffect(exoPlayer, autoPlay) {
        if (autoPlay) {
            exoPlayer.playWhenReady = true
            exoPlayer.play()
        } else {
            exoPlayer.playWhenReady = false
            exoPlayer.pause()
        }
    }

    // 在组件销毁时释放播放器
    DisposableEffect(Unit) {
        onDispose {
            exoPlayer.release()
        }
    }

    AndroidView(
        factory = { ctx ->
            PlayerView(ctx).apply {
                player = exoPlayer
                layoutParams = FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT
                )
                useController = showControls
                // 使用传入的缩放模式
                this.resizeMode = resizeMode
                setShowBuffering(PlayerView.SHOW_BUFFERING_WHEN_PLAYING)
                // 设置控制器超时时间
                controllerShowTimeoutMs = 5000
                // 设置最小高度以确保播放器可见
                if (resizeMode == androidx.media3.ui.AspectRatioFrameLayout.RESIZE_MODE_FIXED_WIDTH) {
                    minimumHeight = (200 * resources.displayMetrics.density).toInt()
                }
            }
        },
        modifier = modifier
    )
}

/**
 * 视频播放器卡片组件
 */
@Composable
fun VideoPlayerCard(
    videoPath: String,
    title: String,
    modifier: Modifier = Modifier,
    autoPlay: Boolean = true,
    aspectRatio: Float? = null // 可选的固定宽高比，null表示自适应
) {
    val isSystemUri = videoPath.startsWith("content://")
    val videoExists = remember(videoPath) {
        if (isSystemUri) {
            true // 系统URI假设存在
        } else {
            File(videoPath).exists()
        }
    }

    Card(
        modifier = modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column {
            // 视频播放区域
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .then(
                        if (aspectRatio != null) {
                            Modifier.aspectRatio(aspectRatio)
                        } else {
                            // 自适应高度，让视频决定自己的尺寸
                            Modifier.wrapContentHeight()
                        }
                    )
            ) {
                if (videoExists) {
                    VideoPlayer(
                        videoPath = videoPath,
                        autoPlay = autoPlay,
                        showControls = true,
                        modifier = Modifier.fillMaxSize()
                    )
                } else {
                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = MaterialTheme.colorScheme.surfaceVariant
                    ) {
                        Column(
                            modifier = Modifier.fillMaxSize(),
                            verticalArrangement = Arrangement.Center,
                            horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = "视频文件不存在",
                                style = MaterialTheme.typography.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = videoPath,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }

            // 视频标题（可选）
            if (title.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                )
            }
        }
    }
}

/**
 * 竖屏模式优化的视频播放器
 * 视频宽度始终等于屏幕宽度，高度根据视频比例自适应
 */
@Composable
fun PortraitVideoPlayer(
    videoPath: String,
    modifier: Modifier = Modifier,
    autoPlay: Boolean = true,
    showControls: Boolean = true
) {
    Box(
        modifier = modifier.fillMaxWidth()
    ) {
        VideoPlayer(
            videoPath = videoPath,
            autoPlay = autoPlay,
            showControls = showControls,
            resizeMode = androidx.media3.ui.AspectRatioFrameLayout.RESIZE_MODE_FIXED_WIDTH,
            modifier = Modifier.fillMaxWidth()
        )
    }
}

/**
 * 全屏视频播放器组件（抖音风格）
 * 播放器占满整个屏幕，视频内容居中显示，进度条在底部
 */
@androidx.annotation.OptIn(UnstableApi::class)
@Composable
fun FullscreenVideoPlayer(
    videoPath: String,
    modifier: Modifier = Modifier,
    autoPlay: Boolean = true,
    showControls: Boolean = true
) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    // 创建 ExoPlayer 实例
    val exoPlayer = remember(videoPath) {
        ExoPlayer.Builder(context)
            .build()
            .apply {
                val uri = when {
                    videoPath.startsWith("content://") -> android.net.Uri.parse(videoPath)
                    videoPath.startsWith("http://") || videoPath.startsWith("https://") ->
                        android.net.Uri.parse(videoPath.replace(" ", "%20"))

                    else -> android.net.Uri.fromFile(File(videoPath))
                }
                val mediaItem = MediaItem.fromUri(uri)
                setMediaItem(mediaItem)
                prepare()
                playWhenReady = false
            }
    }

    // 永久进度条：定时刷新播放进度
    var progress by remember(videoPath) { mutableStateOf(0f) }
    LaunchedEffect(exoPlayer) {
        while (true) {
            val durationMs = exoPlayer.duration
            val positionMs = exoPlayer.currentPosition
            progress = if (durationMs > 0) {
                (positionMs.toFloat() / durationMs.toFloat()).coerceIn(0f, 1f)
            } else {
                0f
            }
            delay(200)
        }
    }

    // 拖动 seek 时的时间浮层
    var isSeekOverlayVisible by remember(videoPath) { mutableStateOf(false) }
    var seekOverlayPositionMs by remember(videoPath) { mutableStateOf(0L) }
    var hideSeekOverlayJob by remember(videoPath) { mutableStateOf<Job?>(null) }

    // 用户正在拖动 seek：此时应暂停播放，且不要被 autoPlay 立即恢复
    var isUserSeeking by remember(videoPath) { mutableStateOf(false) }
    var wasPlayingBeforeSeek by remember(videoPath) { mutableStateOf(false) }

    fun formatTimeMs(timeMs: Long): String {
        val totalSec = (timeMs / 1000L).coerceAtLeast(0L)
        val sec = (totalSec % 60L).toInt()
        val min = ((totalSec / 60L) % 60L).toInt()
        val hour = (totalSec / 3600L).toInt()
        return if (hour > 0) {
            String.format("%d:%02d:%02d", hour, min, sec)
        } else {
            String.format("%02d:%02d", min, sec)
        }
    }

    // 响应 autoPlay 的变化：非活动页暂停；活动页播放（但用户拖动 seek 时不自动播放）
    LaunchedEffect(exoPlayer, autoPlay, isUserSeeking) {
        if (autoPlay && !isUserSeeking) {
            exoPlayer.playWhenReady = true
            exoPlayer.play()
        } else {
            exoPlayer.playWhenReady = false
            exoPlayer.pause()
        }
    }

    // 在组件销毁时释放播放器
    DisposableEffect(videoPath) {
        onDispose {
            exoPlayer.release()
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            // 屏幕中间左右滑动来拖动进度条（seek）
            .pointerInput(exoPlayer) {
                awaitEachGesture {
                    val down = awaitFirstDown(requireUnconsumed = false)

                    // 仅在屏幕中间区域生效，避免和顶部/底部 UI 冲突
                    val y = down.position.y
                    val middleTop = size.height * 0.25f
                    val middleBottom = size.height * 0.75f
                    if (y !in middleTop..middleBottom) {
                        return@awaitEachGesture
                    }

                    val durationMs = exoPlayer.duration
                    if (durationMs <= 0) {
                        return@awaitEachGesture
                    }

                    val startPosMs = exoPlayer.currentPosition
                    var totalDx = 0f
                    var isSeeking = false

                    val touchSlop = viewConfiguration.touchSlop

                    while (true) {
                        val event = awaitPointerEvent()
                        val change = event.changes.firstOrNull() ?: break

                        if (change.changedToUpIgnoreConsumed()) {
                            break
                        }

                        val dx = change.positionChange().x
                        val dy = change.positionChange().y

                        if (!isSeeking) {
                            // 只有横向手势明显时才接管事件，避免影响上下滑动翻页
                            if (abs(dx) < touchSlop) {
                                continue
                            }
                            if (abs(dx) <= abs(dy) * 1.2f) {
                                // 更像纵向滑动：不 consume，让父级 VerticalPager 处理
                                break
                            }
                            isSeeking = true

                            // 开始 seek：显示浮层
                            hideSeekOverlayJob?.cancel()
                            isSeekOverlayVisible = true

                            // 拖动时暂停（松手再按之前状态恢复）
                            isUserSeeking = true
                            wasPlayingBeforeSeek =
                                exoPlayer.isPlaying || exoPlayer.playWhenReady
                            exoPlayer.playWhenReady = false
                            exoPlayer.pause()
                        }

                        // 已进入 seek 模式：consume 并更新进度
                        totalDx += dx
                        change.consume()

                        // 满屏拖动=总时长30%
                        val fraction = (totalDx / size.width.toFloat()).coerceIn(-1f, 1f)
                        val seekRangeMs = (durationMs * 0.30f).toLong().coerceAtLeast(1L)
                        val targetMs = (startPosMs + (fraction * seekRangeMs).toLong())
                            .coerceIn(0L, durationMs)
                        exoPlayer.seekTo(targetMs)

                        // 更新浮层时间
                        seekOverlayPositionMs = targetMs
                    }

                    // 手指抬起后稍微延迟隐藏（更像抖音手感）
                    if (isSeeking) {
                        hideSeekOverlayJob?.cancel()
                        hideSeekOverlayJob = coroutineScope.launch {
                            delay(600)
                            isSeekOverlayVisible = false
                        }

                        // 松手：如果拖动前在播放且当前页允许 autoPlay，则恢复播放
                        isUserSeeking = false
                        if (wasPlayingBeforeSeek && autoPlay) {
                            exoPlayer.playWhenReady = true
                            exoPlayer.play()
                        }
                    }
                }
            },
        contentAlignment = Alignment.Center
    ) {
        AndroidView(
            factory = { ctx ->
                PlayerView(ctx).apply {
                    player = exoPlayer
                    layoutParams = FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                    // 移除所有默认控件
                    useController = false
                    // 使用FIT模式：保持视频比例，视频内容居中
                    this.resizeMode = androidx.media3.ui.AspectRatioFrameLayout.RESIZE_MODE_FIT
                    // 不显示缓冲圈（用户拖动时也不出现“转圈”控件）
                    setShowBuffering(PlayerView.SHOW_BUFFERING_NEVER)
                }
            },
            modifier = Modifier.fillMaxSize()
        )

        // 永久显示进度条（不显示任何其他控件）
        LinearProgressIndicator(
            progress = { progress },
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .navigationBarsPadding()
                .height(4.dp),
            color = androidx.compose.ui.graphics.Color.White,
            trackColor = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.25f)
        )

        // 拖动时显示时间进度（屏幕中间）
        if (isSeekOverlayVisible) {
            Surface(
                modifier = Modifier
                    .align(Alignment.Center)
                    .padding(horizontal = 16.dp),
                color = androidx.compose.ui.graphics.Color.Black.copy(alpha = 0.55f),
                shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = "${formatTimeMs(seekOverlayPositionMs)} / ${formatTimeMs(exoPlayer.duration)}",
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                    style = MaterialTheme.typography.labelLarge,
                    color = androidx.compose.ui.graphics.Color.White
                )
            }
        }
    }
}

/**
 * 全宽度视频播放器组件（用于详情页面）
 */
@Composable
fun FullWidthVideoPlayer(
    videoPath: String,
    modifier: Modifier = Modifier,
    autoPlay: Boolean = true
) {
    VideoPlayer(
        videoPath = videoPath,
        autoPlay = autoPlay,
        showControls = true,
        resizeMode = androidx.media3.ui.AspectRatioFrameLayout.RESIZE_MODE_FIT,
        modifier = modifier.fillMaxWidth()
    )
}

/**
 * 带错误处理的竖屏视频播放器组件
 * @param fullscreen 是否全屏模式（抖音风格：播放器占满屏幕，视频内容居中）
 */
@Composable
fun PortraitVideoPlayerWithErrorHandling(
    videoPath: String,
    title: String = "",
    modifier: Modifier = Modifier,
    autoPlay: Boolean = true,
    fullscreen: Boolean = false
) {
    val isSystemUri = videoPath.startsWith("content://")
    val isNetworkUrl = videoPath.startsWith("http://") || videoPath.startsWith("https://")
    val videoExists = remember(videoPath) {
        when {
            isSystemUri -> true // 系统URI假设存在
            isNetworkUrl -> true // 网络URL假设存在（由网络请求处理）
            else -> File(videoPath).exists()
        }
    }

    if (videoExists) {
        if (fullscreen) {
            // 全屏模式：视频播放器占满屏幕，视频内容居中（抖音风格）
            FullscreenVideoPlayer(
                videoPath = videoPath,
                autoPlay = autoPlay,
                showControls = false,
                modifier = modifier
            )
        } else {
            Column(
                modifier = modifier.fillMaxWidth()
            ) {
                // 视频播放器
                PortraitVideoPlayer(
                    videoPath = videoPath,
                    autoPlay = autoPlay,
                    showControls = true,
                    modifier = Modifier.fillMaxWidth()
                )

                // 可选标题
                if (title.isNotEmpty()) {
                    Text(
                        text = title,
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                    )
                }
            }
        }
    } else {
        // 文件不存在的错误状态
        Card(
            modifier = modifier
                .fillMaxWidth()
                .height(200.dp)
                .padding(horizontal = 16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
        ) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                Column(
                    horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    androidx.compose.material3.Icon(
                        imageVector = androidx.compose.material.icons.Icons.Default.PlayArrow,
                        contentDescription = "视频不存在",
                        modifier = Modifier.size(64.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "视频文件不存在",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    if (title.isNotEmpty()) {
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = title,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}
