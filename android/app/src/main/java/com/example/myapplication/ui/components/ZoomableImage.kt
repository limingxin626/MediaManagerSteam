package com.example.myapplication.ui.components

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import coil.compose.AsyncImage
import coil.request.ImageRequest

/**
 * 可缩放图片组件 — 支持双指缩放、双击切换、拖拽平移
 *
 * 基于 ZoomableContainer 实现，图片最大缩放 5x。
 */
@Composable
fun ZoomableImage(
    imagePath: String?,
    onScaleChanged: (Float) -> Unit,
    modifier: Modifier = Modifier
) {
    ZoomableContainer(
        modifier = modifier,
        maxScale = 5f,
        onScaleChanged = onScaleChanged
    ) {
        AsyncImage(
            model = ImageRequest.Builder(LocalContext.current)
                .data(imagePath)
                .crossfade(true)
                .build(),
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxSize()
        )
    }
}
