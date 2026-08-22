## Why

Android Media 页面已经直接浏览 MediaStore，但建立 Message 仍依赖系统 Photo Picker，并把媒体复制到应用私有目录。用户需要直接在当前媒体网格中批量选择系统媒体、建立一条 Message，并让 Message 持续引用原始 MediaStore 项，避免重复占用本机存储。

## What Changes

- Media 网格支持长按进入多选模式，并选中长按起始项。
- 多选模式支持手指拖过网格项目时连续选择，已处理项目在同一次拖动中不重复切换。
- 多选模式底部显示浮动操作栏，提供选中数量、“创建”和“取消”。
- “创建”将全部选中媒体按网格顺序组成一条 Message，并复用现有本地优先发送与 `create-from-client` 同步流程。
- Room `Media` 明确记录媒体来源和 MediaStore `content://` URI；系统媒体不复制到应用私有目录，也不生成私有媒体副本。
- 图片/视频展示、文件上传及失败重试统一支持从 `ContentResolver` 读取系统媒体。
- 当系统媒体已删除或授权失效时，已同步媒体回退到远端 URL；未同步媒体显示明确失败状态并允许权限或文件恢复后重试。

## Capabilities

### New Capabilities

- `system-media-message-selection`: 从 Android MediaStore 网格通过长按和滑动多选，直接引用系统媒体建立单条 Message。

### Modified Capabilities

（无）

## Impact

- Android `Media` Room schema 增加媒体来源、content URI 和原始文件名字段，并提升数据库版本。
- `MediaListScreen`、`SystemMediaCard` 和 `MediaViewModel` 增加多选与滑动选择状态。
- `MessageViewModel`、上传 request body、媒体路径解析和失败重试支持 `content://`。
- 现有 backend 上传和 `POST /messages/create-from-client` 协议保持不变。
- 系统媒体收藏和标签覆盖层仍保持 local-only；创建 Message 不自动继承这些标签或收藏状态。
