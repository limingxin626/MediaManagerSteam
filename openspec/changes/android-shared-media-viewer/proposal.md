## Why

Android 的 Room 媒体预览已经具备完整的相册体验，包括图片缩放、视频控制、左右分页、页码和缩略图导航；新接入 MediaStore 的系统媒体预览却维护了另一套简化页面，功能不足且容易继续分叉。应将成熟预览 UI 从 Room 数据加载逻辑中解耦，让两种媒体来源共享同一套交互。

## What Changes

- 新增与 Room、MediaStore 无关的预览媒体模型，统一描述媒体 URI、缩略图、类型、尺寸、时长和可选收藏状态。
- 从 `MediaViewerScreen` 抽取共享预览 UI：全屏控制层、左右分页、页码、缩略图导航、图片缩放和视频播放控制。
- Room `MediaViewerScreen` 保留现有窗口加载、跨消息扩展和收藏写入，只负责映射数据并提供操作回调。
- `SystemMediaDetailScreen` 映射 `SystemMedia` 后复用共享预览 UI，支持完整预览功能，但不显示收藏、不写 Room、不上传。
- 保持现有 MediaStore 列表、路由和无闪烁返回行为。

## Capabilities

### New Capabilities
- `shared-media-viewer`: Android Room 媒体和系统媒体共享完整、数据源无关的媒体预览交互。

### Modified Capabilities

（无已有 spec 需要修改）

## Impact

- `MediaViewerScreen.kt`：数据加载继续保留，预览渲染改由共享组件承担。
- 新增共享 viewer model/component，复用 `ZoomableImage`、`TelegramVideoPlayer` 和现有缩略图实现。
- `SystemMediaDetailScreen.kt`：移除独立简化预览，改为共享 viewer adapter。
- 不改变 Room schema、backend、同步协议或 MediaStore 写入行为。
