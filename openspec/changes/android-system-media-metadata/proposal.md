## Why

Android Media 页面已经直接浏览 MediaStore，但系统文件本身不适合承载应用内收藏与标签。需要一个仅本机的 Room 元数据覆盖层，让用户管理系统媒体，同时保持文件来源和同步边界清晰。

## What Changes

- 新增 `system_media_metadata`，按 SystemMedia stableKey 保存 content URI 和收藏状态。
- 新增 `system_media_tag`，连接 stableKey 与现有 `Tag` 表。
- Media 页面将 MediaStore 数据与 Room 元数据合并，显示并切换收藏，编辑标签。
- 支持按收藏和单个标签筛选系统媒体。
- 系统媒体预览显示本机收藏操作和标签编辑入口。
- 元数据严格本机保存，不修改 MediaStore、不复制文件、不进入 Outbox 或 backend 同步。

## Capabilities

### New Capabilities
- `system-media-metadata`: 为 MediaStore 媒体提供本机收藏、标签编辑和筛选。

### Modified Capabilities

（无）

## Impact

- Room schema 版本提升并新增两个实体与 DAO。
- `DatabaseManager` 新增本机 metadata repository。
- `MediaViewModel` 合并 MediaStore 与 metadata/tag flow。
- `MediaListScreen`、`SystemMediaDetailScreen` 和共享 viewer 增加系统媒体元数据 UI。
- backend、同步协议和 MediaStore 文件不受影响。
