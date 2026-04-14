## Why

MediaViewerScreen 目前仅以 `ContentScale.Fit` 静态显示图片，用户无法放大查看细节。对于高分辨率图片和视频截图，这是基本的浏览体验缺失。Instagram、Telegram 等主流应用均支持双击/双指缩放，用户已形成肌肉记忆。

## What Changes

- 图片预览支持双指缩放（pinch-to-zoom），缩放范围 1x–5x
- 图片预览支持双击快速切换放大/还原（toggle 2x ↔ 1x）
- 放大状态下支持单指拖拽平移（pan）查看细节
- 放大状态下禁止 HorizontalPager 左右翻页手势，还原后恢复翻页
- 视频播放页不受影响，保持现有交互行为

## Capabilities

### New Capabilities
- `image-zoom`: 图片双击/双指缩放与平移交互，包含手势检测、状态管理、与 Pager 的手势协调

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **代码**：`MediaViewerScreen.kt` 中图片显示部分需包裹缩放容器；可能新增 `ZoomableImage` composable
- **依赖**：无新依赖，使用 Compose 内置 `pointerInput` + `detectTransformGestures` / `detectTapGestures`
- **兼容性**：仅影响图片浏览，视频播放器和缩略图网格不受影响
