## Why

视频预览目前只能1:1观看，无法像图片一样双指缩放、双击放大或拖拽平移。用户在查看视频细节（如字幕、画面角落内容）时体验不佳。图片已实现完整的缩放功能（ZoomableImage），视频应保持一致的交互体验。

## What Changes

- 为 `TelegramVideoPlayer` 添加双指缩放（pinch-to-zoom）支持，范围 1x–3x
- 添加双击切换缩放（1x ↔ 2x）
- 缩放状态下支持单指拖拽平移（pan）
- 缩放状态下禁用 HorizontalPager 的页面滑动，与 ZoomableImage 行为一致
- 确保缩放手势与现有的水平拖拽快进（seek）手势不冲突

## Capabilities

### New Capabilities
- `video-zoom`: 视频播放器的缩放、平移手势支持，包括双指缩放、双击缩放和拖拽平移

### Modified Capabilities

## Impact

- `android/app/src/main/java/com/example/myapplication/ui/components/VideoPlayer.kt` — TelegramVideoPlayer 需要新增缩放手势层
- `android/app/src/main/java/com/example/myapplication/ui/screens/media/MediaViewerScreen.kt` — 需要将视频缩放状态纳入 `currentScale` 协调逻辑
- 无新增依赖，复用 Compose Foundation 的 `pointerInput` + `graphicsLayer`
