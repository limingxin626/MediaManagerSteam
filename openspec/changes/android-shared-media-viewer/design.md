## Context

`MediaViewerScreen` 同时包含 Room 数据窗口加载和成熟的预览 UI。后者直接依赖 Room `Media` 与 `DatabaseManager`，导致 `SystemMediaDetailScreen` 只能复制一套简化实现。已有通用底层组件 `ZoomableImage`、`TelegramVideoPlayer` 可直接处理文件、网络 URL 和 `content://` URI。

## Goals / Non-Goals

**Goals:**
- Room 与 MediaStore 使用同一套预览布局和手势。
- 保持 Room 预览当前行为，包括窗口扩展和收藏。
- 系统媒体获得缩放、视频控制、分页、页码、缩略图和全屏控制栏。
- 系统预览保持只读，不创建 Room 数据。

**Non-Goals:**
- 改变媒体列表、MediaStore 查询或权限策略。
- 为系统媒体新增收藏、标签、删除或编辑。
- 重写底层缩放或播放器组件。

## Decisions

### 1. 使用中立 ViewerMediaItem

新增轻量 UI model，字段仅覆盖渲染需要：稳定 key、媒体 URI、缩略图 URI、mimeType、宽高、时长和可选 starred。Room `Media` 与 `SystemMedia` 分别通过映射函数转换。

### 2. 抽取纯 UI SharedMediaViewer

共享组件接收 item 列表、初始 key、可选收藏回调及关闭回调。它内部负责 pager、缩放比例与分页冲突、视频控制状态、页码和缩略图条，不访问 repository 或 DatabaseManager。

### 3. 数据加载保留在 adapter screen

Room screen 保留现有三种加载模式及窗口扩展逻辑，然后把当前窗口映射给共享 UI。系统 screen 使用 `MediaViewModel` 已加载列表；若进程恢复导致列表为空，则按 URI 查询单项作为 fallback。

### 4. 可选能力通过 nullable callback 表达

当 `onToggleStar` 为 null 时不显示收藏按钮。共享 viewer 不执行持久化；Room adapter 可提供原收藏操作，系统 adapter 也可提供独立的本机 metadata 收藏回调。

## Risks / Trade-offs

- 抽取时可能影响 Room viewer 手势或窗口扩展，需保持其 state ownership 和扩展回调。
- 系统媒体列表可能很大，共享 viewer 继续使用 `beyondViewportPageCount=0`，缩略图按可见项加载。
- 图片缩放时必须禁用 pager 滑动，避免手势冲突。

## Migration Plan

1. 引入中立模型和共享组件。
2. 将 Room viewer 的渲染部分替换为共享组件，验证行为无回归。
3. 将系统详情替换为共享组件。
4. 运行测试和构建并进行手势检查。
