## 1. 提取通用缩放容器

- [x] 1.1 从 ZoomableImage.kt 提取缩放状态管理和手势处理逻辑为 `ZoomableContainer` composable（参数：maxScale、onScaleChanged、content slot）
- [x] 1.2 重构 ZoomableImage 使用 ZoomableContainer 包裹 AsyncImage，确保行为不变

## 2. 视频播放器集成缩放

- [x] 2.1 在 TelegramVideoPlayer 外层用 ZoomableContainer 包裹（maxScale = 3f），通过 graphicsLayer 应用缩放变换
- [x] 2.2 处理手势冲突：scale > 1x 时禁用 seek 拖拽，将单指拖拽路由到平移；scale = 1x 时保持原有 seek 行为

## 3. Pager 协调

- [x] 3.1 在 MediaViewerScreen 中将视频的 ZoomableContainer 的 onScaleChanged 回调接入 currentScale 状态，实现缩放时禁用 HorizontalPager 滑动
- [x] 3.2 确保翻页时视频缩放状态重置为 1x（LaunchedEffect(settledPage) 已有此逻辑，验证对视频同样生效）
