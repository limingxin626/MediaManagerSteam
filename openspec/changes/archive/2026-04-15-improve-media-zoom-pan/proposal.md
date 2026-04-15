## Why

当前媒体预览器的缩放与平移功能存在三个体验问题：
1. **居中约束不足**：当媒体未填满屏幕某一边时（如竖屏下的横向视频），放大过程中媒体可能偏离中心，应保持在未填满方向上始终居中。
2. **平移边界不正确**：当前 `calculateBounds` 基于容器尺寸而非媒体实际尺寸计算边界，导致放大后拖拽可能露出媒体内容外的空白区域。
3. **控件与缩略图条的显隐不统一**：图片单击应切换缩略图条显隐；视频的进度条控件与缩略图条应同步出现和消失。

## What Changes

- 修改 `ZoomableContainer` 的边界计算逻辑，引入媒体实际宽高比（aspect ratio），在媒体未填满容器某一方向时锁定该方向的 offset 为 0（居中），并基于媒体实际覆盖区域（而非容器尺寸）计算平移边界
- 修改 `MediaViewerScreen` 的缩略图条（`MediaStripBar`）显隐逻辑：
  - 图片页面：单击切换缩略图条的显示与隐藏
  - 视频页面：缩略图条与视频控件（播放按钮、进度条）同步显隐
- 调整 `ZoomableImage` 和 `TelegramVideoPlayer` 传递媒体宽高信息给 `ZoomableContainer`

## Capabilities

### New Capabilities
- `media-viewer-controls-sync`: 统一管理 MediaViewerScreen 中控件（进度条、播放按钮）与缩略图条的显隐同步逻辑

### Modified Capabilities
- `image-zoom`: 修改平移边界计算，引入媒体宽高比感知的居中约束和边界限制

## Impact

- **修改文件**：
  - `ZoomableContainer.kt` — 核心边界计算与居中逻辑
  - `ZoomableImage.kt` — 传递媒体尺寸参数
  - `VideoPlayer.kt` — 暴露控件可见性状态供外部同步
  - `MediaViewerScreen.kt` — 缩略图条显隐状态管理、单击回调
- **无 API 变更**，纯客户端改动
- **无新依赖**
