## Why

媒体预览界面（MediaViewerScreen）的控件显隐和拖拽交互存在三个未修复的 bug，影响用户体验：
1. 缩略图条的显隐状态在滑动切换页面时不持续——当前页隐藏后切到下一页又显示，交替反复；
2. 视频播放器的控件（播放按钮、时间、进度条）无法被隐藏，单击画面隐藏控件对视频页无效；
3. 放大后拖拽平移缺乏惯性动量（fling），松手后立即停止，手感僵硬。

## What Changes

- **修复控件显隐状态跨页面不持续**：将 `controlsVisible` 状态提升为跨页面共享的单一来源，确保视频组件接收并尊重外部传入的可见性状态，而非各自维护独立的初始值。
- **修复视频控件无法隐藏**：让 `TelegramVideoPlayer` 接受外部控制的 `controlsVisible` 状态（双向同步），而非仅单向回调。当屏幕级别的 `controlsVisible` 被设为 false 时，视频内部的控件也必须响应隐藏。
- **为放大拖拽添加 fling 惯性**：在 `ZoomableContainer` 和 `TelegramVideoPlayer` 的缩放拖拽手势中，追踪手指速度，松手后使用 `exponentialDecay` 或 `splineBasedDecay` 动画模拟惯性滑动，并在边界处自然停止。

## Capabilities

### New Capabilities
- `zoom-pan-fling`: 放大状态下拖拽松手后添加速度衰减惯性动画

### Modified Capabilities
- `media-viewer-controls-sync`: 修复缩略图条显隐状态跨页不持续、视频控件无法隐藏的问题

## Impact

- `android/app/src/main/java/.../ui/screens/media/MediaViewerScreen.kt` — 控件状态管理改为双向同步
- `android/app/src/main/java/.../ui/components/VideoPlayer.kt` — `TelegramVideoPlayer` 接受外部 controlsVisible 参数
- `android/app/src/main/java/.../ui/components/ZoomableContainer.kt` — 添加 fling 惯性动画
- 无 API 变更，无数据库变更，无新依赖
