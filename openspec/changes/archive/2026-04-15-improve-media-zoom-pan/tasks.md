## 1. ZoomableContainer 边界计算改造

- [x] 1.1 为 `ZoomableContainer` 添加 `mediaAspectRatio: Float?` 参数，默认值 `null`（退化为当前行为）
- [x] 1.2 重写 `calculateBounds`：基于 `mediaAspectRatio` 和 `containerSize` 计算媒体实际渲染尺寸（`fitWidth/fitHeight`），然后基于 `scaledMedia - container` 计算各方向最大偏移，未超出方向锁定为 0
- [x] 1.3 验证：竖屏下横向视频放大时水平方向保持居中，直到缩放后宽度超过屏幕宽度才允许水平平移
- [x] 1.4 验证：放大后拖拽到极限位置时，媒体边缘不离开屏幕边缘，无空白区域

## 2. 媒体宽高比传递

- [x] 2.1 修改 `ZoomableImage`：通过 Coil 的 `painter.intrinsicSize` 获取图片实际宽高，计算 aspect ratio 传递给 `ZoomableContainer`
- [x] 2.2 修改 `TelegramVideoPlayer`（`zoomEnabled=true` 模式）：通过 ExoPlayer 的 `videoSize` 回调获取视频实际宽高，计算 aspect ratio 传递给缩放逻辑

## 3. 控件与缩略图条显隐同步

- [x] 3.1 在 `MediaViewerScreen` 中添加 `controlsVisible` 状态（默认 `true`），传递给 `MediaStripBar` 控制其 `AnimatedVisibility`
- [x] 3.2 图片页面：将 `ZoomableContainer.onSingleTap` 回调设为切换 `controlsVisible`
- [x] 3.3 视频页面：为 `TelegramVideoPlayer` 添加 `onControlsVisibilityChanged: (Boolean) -> Unit` 回调，在控件显隐变化时通知 `MediaViewerScreen` 同步更新 `controlsVisible`
- [x] 3.4 确保视频 3 秒自动隐藏时缩略图条同步隐藏
- [x] 3.5 确保缩略图条显隐状态跨页面滑动保持一致
