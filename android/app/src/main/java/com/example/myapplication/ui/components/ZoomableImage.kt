package com.example.myapplication.ui.components

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.VectorConverter
import androidx.compose.animation.core.spring
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.detectTapGestures
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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.IntSize
import coil.compose.AsyncImage
import coil.request.ImageRequest
import kotlinx.coroutines.launch
import kotlin.math.abs

private const val MIN_SCALE = 1f
private const val MAX_SCALE = 5f
private const val DOUBLE_TAP_SCALE = 2f

/**
 * 可缩放图片组件 — 支持双指缩放、双击切换、拖拽平移
 *
 * 关键设计：在 scale == 1x 且单指拖拽时不消费手势，让 HorizontalPager 正常处理翻页。
 * 仅在以下情况消费手势：
 * - 双指触摸（pinch-to-zoom）
 * - scale > 1x 时的单指拖拽（pan）
 */
@Composable
fun ZoomableImage(
    imagePath: String?,
    onScaleChanged: (Float) -> Unit,
    modifier: Modifier = Modifier
) {
    val scope = rememberCoroutineScope()
    val scale = remember { Animatable(1f) }
    val offset = remember { Animatable(Offset.Zero, Offset.VectorConverter) }
    var containerSize by remember { mutableStateOf(IntSize.Zero) }

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

    Box(
        modifier = modifier
            .onSizeChanged { containerSize = it }
            // 双指缩放 + 放大后拖拽（手动手势处理，避免消费单指水平滑动）
            .pointerInput(Unit) {
                awaitEachGesture {
                    // 等待第一个手指按下
                    val firstDown = awaitFirstDown(requireUnconsumed = false)
                    var pointerId = firstDown.id
                    var pastTouchSlop = false
                    var didTransform = false

                    while (true) {
                        val event = awaitPointerEvent(PointerEventPass.Main)
                        val activePointers = event.changes.filter { it.pressed }

                        if (activePointers.isEmpty()) {
                            // 所有手指抬起 — 弹回处理
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
                            }
                            break
                        }

                        if (activePointers.size >= 2) {
                            // ── 双指：pinch-to-zoom ──
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
                                    val newScale = (scale.value * zoomFactor).coerceIn(0.5f, MAX_SCALE)
                                    scale.snapTo(newScale)
                                    if (newScale > 1f) {
                                        offset.snapTo(clampOffset(offset.value + pan))
                                    } else {
                                        offset.snapTo(Offset.Zero)
                                    }
                                }
                                didTransform = true
                            }
                            // 消费所有指针变化，阻止 Pager 拦截
                            event.changes.forEach { it.consume() }

                        } else if (scale.value > 1.01f) {
                            // ── 单指 + 已放大：pan ──
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
            }
            // 双击缩放
            .pointerInput(Unit) {
                detectTapGestures(
                    onDoubleTap = { tapOffset ->
                        scope.launch {
                            if (scale.value > 1.01f) {
                                // 已放大 → 还原
                                launch { scale.animateTo(MIN_SCALE, spring()) }
                                launch { offset.animateTo(Offset.Zero, spring()) }
                            } else {
                                // 1x → 放大到 2x，以点击位置为中心
                                val cx = containerSize.width / 2f
                                val cy = containerSize.height / 2f
                                val targetOffset = Offset(
                                    (cx - tapOffset.x) * (DOUBLE_TAP_SCALE - 1f),
                                    (cy - tapOffset.y) * (DOUBLE_TAP_SCALE - 1f)
                                )
                                val clampedTarget = clampOffset(targetOffset, DOUBLE_TAP_SCALE)
                                launch { scale.animateTo(DOUBLE_TAP_SCALE, spring()) }
                                launch { offset.animateTo(clampedTarget, spring()) }
                            }
                        }
                    }
                )
            },
        contentAlignment = Alignment.Center
    ) {
        AsyncImage(
            model = ImageRequest.Builder(LocalContext.current)
                .data(imagePath)
                .crossfade(true)
                .build(),
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer {
                    scaleX = scale.value
                    scaleY = scale.value
                    translationX = offset.value.x
                    translationY = offset.value.y
                }
        )
    }
}
