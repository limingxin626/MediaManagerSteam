package com.example.myapplication.ui.navigation

import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally

/**
 * 导航动画配置
 */
object NavigationAnimations {

    // 定义动画持续时间
    private const val ANIMATION_DURATION = 400
    private const val TAB_ANIMATION_DURATION = 300

    // 页面间导航动画（前进）
    fun slideInFromRight(): EnterTransition {
        return slideInHorizontally(
            initialOffsetX = { fullWidth -> fullWidth },
            animationSpec = tween(
                durationMillis = ANIMATION_DURATION,
                easing = FastOutSlowInEasing
            )
        ) + fadeIn(
            animationSpec = tween(
                durationMillis = ANIMATION_DURATION / 2,
                easing = FastOutSlowInEasing
            )
        )
    }

    fun slideOutToLeft(): ExitTransition {
        return slideOutHorizontally(
            targetOffsetX = { fullWidth -> -fullWidth },
            animationSpec = tween(
                durationMillis = ANIMATION_DURATION,
                easing = FastOutSlowInEasing
            )
        ) + fadeOut(
            animationSpec = tween(
                durationMillis = ANIMATION_DURATION / 2,
                easing = FastOutSlowInEasing
            )
        )
    }

    // 返回导航动画（后退）
    fun slideInFromLeft(): EnterTransition {
        return slideInHorizontally(
            initialOffsetX = { fullWidth -> -fullWidth },
            animationSpec = tween(
                durationMillis = ANIMATION_DURATION,
                easing = FastOutSlowInEasing
            )
        ) + fadeIn(
            animationSpec = tween(
                durationMillis = ANIMATION_DURATION / 2,
                easing = FastOutSlowInEasing
            )
        )
    }

    fun slideOutToRight(): ExitTransition {
        return slideOutHorizontally(
            targetOffsetX = { fullWidth -> fullWidth },
            animationSpec = tween(
                durationMillis = ANIMATION_DURATION,
                easing = FastOutSlowInEasing
            )
        ) + fadeOut(
            animationSpec = tween(
                durationMillis = ANIMATION_DURATION / 2,
                easing = FastOutSlowInEasing
            )
        )
    }

    // Tab 切换专用：纯滑动，无 fade（更流畅的横向切换感）
    fun tabSlideInFromRight(): EnterTransition {
        return slideInHorizontally(
            initialOffsetX = { fullWidth -> fullWidth },
            animationSpec = tween(
                durationMillis = TAB_ANIMATION_DURATION,
                easing = FastOutSlowInEasing
            )
        )
    }

    fun tabSlideOutToLeft(): ExitTransition {
        return slideOutHorizontally(
            targetOffsetX = { fullWidth -> -fullWidth },
            animationSpec = tween(
                durationMillis = TAB_ANIMATION_DURATION,
                easing = FastOutSlowInEasing
            )
        )
    }

    fun tabSlideInFromLeft(): EnterTransition {
        return slideInHorizontally(
            initialOffsetX = { fullWidth -> -fullWidth },
            animationSpec = tween(
                durationMillis = TAB_ANIMATION_DURATION,
                easing = FastOutSlowInEasing
            )
        )
    }

    fun tabSlideOutToRight(): ExitTransition {
        return slideOutHorizontally(
            targetOffsetX = { fullWidth -> fullWidth },
            animationSpec = tween(
                durationMillis = TAB_ANIMATION_DURATION,
                easing = FastOutSlowInEasing
            )
        )
    }

    // 渐入渐出动画（用于全屏媒体等特殊场景）
    fun fadeIn(durationMillis: Int = 300): EnterTransition {
        return fadeIn(tween(durationMillis))
    }

    fun fadeOut(durationMillis: Int = 300): ExitTransition {
        return fadeOut(tween(durationMillis))
    }

    // 无动画
    fun noAnimation(): EnterTransition = EnterTransition.None
    fun noExitAnimation(): ExitTransition = ExitTransition.None
}