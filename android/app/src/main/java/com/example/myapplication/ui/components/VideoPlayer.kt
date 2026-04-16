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
import androidx.compose.ui.input.pointer.util.VelocityTracker
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
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
    controlsVisible: Boolean = false,
    onScaleChanged: ((Float) -> Unit)? = null,
    onControlsVisibilityChanged: ((Boolean) -> Unit)? = null
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
    var videoAspectRatio by remember { mutableStateOf<Float?>(null) }
    val density = LocalDensity.current
    val flingDecay = remember(density) {
        androidx.compose.animation.splineBasedDecay<Offset>(density)
    }

    LaunchedEffect(zoomScale.value) {
        onScaleChanged?.invoke(zoomScale.value)
    }

    fun calculateBounds(atScale: Float = zoomScale.value): Pair<Offset, Offset> {
        if (containerSize == IntSize.Zero) return Offset.Zero to Offset.Zero
        val cw = containerSize.width.toFloat()
        val ch = containerSize.height.toFloat()

        val (mediaW, mediaH) = if (videoAspectRatio != null && videoAspectRatio!! > 0f) {
            val containerAR = cw / ch
            if (videoAspectRatio!! > containerAR) {
                cw to (cw / videoAspectRatio!!)
            } else {
                (ch * videoAspectRatio!!) to ch
            }
        } else {
            cw to ch
        }

        val scaledW = mediaW * atScale
        val scaledH = mediaH * atScale

        val maxX = if (scaledW <= cw) 0f else (scaledW - cw) / 2f
        val maxY = if (scaledH <= ch) 0f else (scaledH - ch) / 2f

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
            onControlsVisibilityChanged?.invoke(false)
        }
    }

    fun toggleControls() {
        if (controlsVisible) {
            hideControlsJob?.cancel()
            onControlsVisibilityChanged?.invoke(false)
        } else {
            onControlsVisibilityChanged?.invoke(true)
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

    // 外部 controlsVisible 变为 true 时，启动自动隐藏计时
    LaunchedEffect(controlsVisible) {
        if (controlsVisible) {
            scheduleHideControls()
        } else {
            hideControlsJob?.cancel()
        }
    }

    // 播放器状态监听
    DisposableEffect(exoPlayer) {
        val listener = object : Player.Listener {
            override fun onIsPlayingChanged(playing: Boolean) {
                isPlaying = playing
            }

            override fun onVideoSizeChanged(videoSize: androidx.media3.common.VideoSize) {
                if (videoSize.width > 0 && videoSize.height > 0) {
                    videoAspectRatio = videoSize.width.toFloat() / videoSize.height.toFloat()
                }
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
                            val velocityTracker = VelocityTracker()

                            while (true) {
                                val event = awaitPointerEvent(PointerEventPass.Main)
                                val activePointers = event.changes.filter { it.pressed }

                                if (activePointers.isEmpty()) {
                                    if (didTransform) {
                                        val velocity = velocityTracker.calculateVelocity()
                                        coroutineScope.launch {
                                            if (zoomScale.value < 1f) {
                                                launch { zoomScale.animateTo(1f, spring()) }
                                                launch {
                                                    zoomOffset.animateTo(
                                                        Offset.Zero,
                                                        spring()
                                                    )
                                                }
                                            } else if (zoomScale.value > 1.01f &&
                                                (kotlin.math.abs(velocity.x) > 50f || kotlin.math.abs(
                                                    velocity.y
                                                ) > 50f)
                                            ) {
                                                // Fling 惯性动画 — 设置边界后启动衰减
                                                val (minBound, maxBound) = calculateBounds()
                                                zoomOffset.updateBounds(minBound, maxBound)
                                                val initialVelocity = Offset(velocity.x, velocity.y)
                                                try {
                                                    zoomOffset.animateDecay(
                                                        initialVelocity,
                                                        flingDecay
                                                    )
                                                } finally {
                                                    zoomOffset.updateBounds(null, null)
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
                                        // 追踪速度用于 fling
                                        velocityTracker.addPosition(
                                            event.changes.first().uptimeMillis,
                                            pointer.position
                                        )
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
