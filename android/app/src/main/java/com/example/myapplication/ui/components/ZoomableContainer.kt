package com.example.myapplication.ui.components

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.VectorConverter
import androidx.compose.animation.core.spring
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.changedToUp
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.positionChanged
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.unit.IntSize
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private const val MIN_SCALE = 1f
private const val DEFAULT_DOUBLE_TAP_SCALE = 2f
private const val DOUBLE_TAP_TIMEOUT_MS = 300L

/**
 * 通用缩放容器 — 支持双指缩放、双击切换、拖拽平移
 *
 * 在 scale == 1x 且单指拖拽时不消费手势，让 HorizontalPager 正常处理翻页。
 * 仅在以下情况消费手势：
 * - 双指触摸（pinch-to-zoom）
 * - scale > 1x 时的单指拖拽（pan）
 *
 * 双击检测使用 requireUnconsumed = false，确保即使子组件消费了点击事件，
 * 双击缩放仍能正常工作（如包裹视频播放器时，内部有点击切换控件手势）。
 *
 * @param maxScale 最大缩放倍率
 * @param onScaleChanged 缩放变化回调（用于与 HorizontalPager 协调）
 * @param onSingleTap 单击回调 — 在确认不是双击后延迟触发（约 300ms），
 *                    用于替代子组件自身的点击处理（如视频控件显示/隐藏）
 * @param content 被缩放的内容
 */
@Composable
fun ZoomableContainer(
    modifier: Modifier = Modifier,
    maxScale: Float = 5f,
    onScaleChanged: (Float) -> Unit = {},
    onSingleTap: (() -> Unit)? = null,
    content: @Composable () -> Unit
) {
    val scope = rememberCoroutineScope()
    val scale = remember { Animatable(1f) }
    val offset = remember { Animatable(Offset.Zero, Offset.VectorConverter) }
    var containerSize by remember { mutableStateOf(IntSize.Zero) }

    // 双击检测状态
    var lastTapTimeMs by remember { mutableStateOf(0L) }
    var lastTapPosition by remember { mutableStateOf(Offset.Zero) }
    var pendingSingleTapJob by remember { mutableStateOf<Job?>(null) }

    // 通知外部 scale 变化
    LaunchedEffect(scale.value) {
        onScaleChanged(scale.value)
    }

    fun calculateBounds(atScale: Float = scale.value): Pair<Offset, Offset> {
        if (containerSize == IntSize.Zero) return Offset.Zero to Offset.Zero
        val maxX = ((atScale - 1f) * containerSize.width / 2f).coerceAtLeast(0f)
        val maxY = ((atScale - 1f) * containerSize.height / 2f).coerceAtLeast(0f)
        return Offset(-maxX, -maxY) to Offset(maxX, maxY)
    }

    fun clampOffset(raw: Offset, atScale: Float = scale.value): Offset {
        val (min, max) = calculateBounds(atScale)
        return Offset(
            raw.x.coerceIn(min.x, max.x),
            raw.y.coerceIn(min.y, max.y)
        )
    }

    fun handleDoubleTap(tapOffset: Offset) {
        scope.launch {
            if (scale.value > 1.01f) {
                launch { scale.animateTo(MIN_SCALE, spring()) }
                launch { offset.animateTo(Offset.Zero, spring()) }
            } else {
                val cx = containerSize.width / 2f
                val cy = containerSize.height / 2f
                val targetOffset = Offset(
                    (cx - tapOffset.x) * (DEFAULT_DOUBLE_TAP_SCALE - 1f),
                    (cy - tapOffset.y) * (DEFAULT_DOUBLE_TAP_SCALE - 1f)
                )
                val clampedTarget = clampOffset(targetOffset, DEFAULT_DOUBLE_TAP_SCALE)
                launch { scale.animateTo(DEFAULT_DOUBLE_TAP_SCALE, spring()) }
                launch { offset.animateTo(clampedTarget, spring()) }
            }
        }
    }

    Box(
        modifier = modifier
            .onSizeChanged { containerSize = it }
            // 双指缩放 + 放大后拖拽 + 双击缩放（统一手势处理）
            .pointerInput(Unit) {
                awaitEachGesture {
                    val firstDown = awaitFirstDown(requireUnconsumed = false)
                    var pastTouchSlop = false
                    var didTransform = false

                    while (true) {
                        val event = awaitPointerEvent(PointerEventPass.Main)
                        val activePointers = event.changes.filter { it.pressed }

                        if (activePointers.isEmpty()) {
                            // 所有手指抬起
                            if (didTransform) {
                                scope.launch {
                                    if (scale.value < MIN_SCALE) {
                                        launch { scale.animateTo(MIN_SCALE, spring()) }
                                        launch { offset.animateTo(Offset.Zero, spring()) }
                                    } else {
                                        val clamped = clampOffset(offset.value)
                                        if (clamped != offset.value) {
                                            offset.animateTo(clamped, spring())
                                        }
                                    }
                                }
                            } else {
                                // 没有拖拽/缩放 → 可能是点击，检测双击
                                val upChange = event.changes.firstOrNull { it.changedToUp() }
                                if (upChange != null) {
                                    val now = System.currentTimeMillis()
                                    val tapPos = upChange.position
                                    val timeSinceLast = now - lastTapTimeMs
                                    val distFromLast = (tapPos - lastTapPosition).getDistance()

                                    if (timeSinceLast < DOUBLE_TAP_TIMEOUT_MS && distFromLast < viewConfiguration.touchSlop * 3) {
                                        // 双击 → 取消待执行的单击，执行缩放
                                        pendingSingleTapJob?.cancel()
                                        pendingSingleTapJob = null
                                        handleDoubleTap(tapPos)
                                        lastTapTimeMs = 0L
                                    } else {
                                        // 第一次点击 → 延迟执行单击（等待可能的双击）
                                        lastTapTimeMs = now
                                        lastTapPosition = tapPos
                                        if (onSingleTap != null) {
                                            pendingSingleTapJob?.cancel()
                                            pendingSingleTapJob = scope.launch {
                                                delay(DOUBLE_TAP_TIMEOUT_MS)
                                                onSingleTap()
                                            }
                                        }
                                    }
                                }
                            }
                            break
                        }

                        if (activePointers.size >= 2) {
                            // 双指：pinch-to-zoom
                            val pointer1 = activePointers[0]
                            val pointer2 = activePointers[1]
                            val prevPos1 = pointer1.previousPosition
                            val prevPos2 = pointer2.previousPosition
                            val curPos1 = pointer1.position
                            val curPos2 = pointer2.position

                            val prevDist = (prevPos1 - prevPos2).getDistance()
                            val curDist = (curPos1 - curPos2).getDistance()

                            if (prevDist > 0f && curDist > 0f) {
                                val zoomFactor = curDist / prevDist
                                val centroid = (curPos1 + curPos2) / 2f
                                val prevCentroid = (prevPos1 + prevPos2) / 2f
                                val pan = centroid - prevCentroid

                                scope.launch {
                                    val newScale =
                                        (scale.value * zoomFactor).coerceIn(0.5f, maxScale)
                                    scale.snapTo(newScale)
                                    if (newScale > 1f) {
                                        offset.snapTo(clampOffset(offset.value + pan))
                                    } else {
                                        offset.snapTo(Offset.Zero)
                                    }
                                }
                                didTransform = true
                            }
                            event.changes.forEach { it.consume() }

                        } else if (scale.value > 1.01f) {
                            // 单指 + 已放大：pan
                            val pointer = activePointers.first()
                            val pan = pointer.position - pointer.previousPosition

                            if (!pastTouchSlop) {
                                val dist = (pointer.position - firstDown.position).getDistance()
                                if (dist > viewConfiguration.touchSlop) {
                                    pastTouchSlop = true
                                }
                            }

                            if (pastTouchSlop && pointer.positionChanged()) {
                                scope.launch {
                                    offset.snapTo(clampOffset(offset.value + pan))
                                }
                                didTransform = true
                                event.changes.forEach { it.consume() }
                            }
                        }
                        // else: scale <= 1 且单指 → 不消费，Pager 处理翻页
                    }
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer {
                    scaleX = scale.value
                    scaleY = scale.value
                    translationX = offset.value.x
                    translationY = offset.value.y
                }
        ) {
            content()
        }
    }
}
