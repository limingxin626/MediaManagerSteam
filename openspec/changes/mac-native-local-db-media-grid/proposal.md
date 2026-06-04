## Why

当前 Mac 客户端是 SwiftUI UI + HTTP 调用本地 Python backend 的薄壳实现,跟 Vue/Electron 共享同一套后端。新的定位是 **Mac 作为主力端、Android 作为辅助、不再有 Windows 和网页端**,Mac 不需要再依赖 Python 进程——可以拿到原生分发(单 .app)、更快冷启动、QuickLook/AVKit/Spotlight 等系统集成,以及砍掉 uvicorn 常驻进程的资源占用。

多端之间不必功能完全一致,只要**数据库 schema 保持一致**(同一个 `db.sqlite3` 文件 + `data/thumbs/` + `uploads/` 目录布局),Mac 端就可以完全本机直读 SQLite,不经过 backend。本次只做第一期 —— **媒体网格的本地化只读**,不涉及多设备同步、不涉及写操作。

## What Changes

- 新增 **本地数据库通路**:Mac app 通过 GRDB.swift 直接打开 `DATA_ROOT/db.sqlite3`(只读模式),不再经过 HTTP
- 新增 **DATA_ROOT 配置**:首次启动用 `NSOpenPanel` 让用户选数据根目录,持久化到 `UserDefaults`
- 新增 **`MediaSource` 抽象层**:在 `APIMediaSource`(现有)与 `LocalMediaSource`(新)之间可切换,默认走本地
- 新增 **本地缩略图/媒体文件加载**:`AsyncImage(url:)` 改为读 `DATA_ROOT/data/thumbs/{id}.webp`,视频走 `AVPlayer(url: localFileURL)`
- 修改 **`MediaLibraryViewModel`**:构造函数接受 `MediaSource` 协议,业务逻辑不变(分页、类型过滤、starred 过滤)
- 修改 **媒体分页游标语义**:本地版从 backend 的 `{created_at}|{position}` 复合游标改为 `{created_at}|{id}`(本地查的是裸 `Media` 表,不经过 `MessageMedia` junction)
- 新增 **QuickLook 集成**(加分项):空格键预览选中的媒体
- 删除/停用 **`FeedView` / `FeedViewModel`**:第一期不做 message feed,先聚焦媒体网格

**非目标(明确不做)**:
- 不做任何写操作(收藏切换、删除、上传等),仍保留 HTTP 路径但 UI 上隐藏入口
- 不做多设备同步(iCloud/Syncthing 适配)
- 不做 ffmpeg 缩略图生成、不做 Blake2b 去重 —— 这些仍由 backend / Android 负责
- 不做 Message/Actor/Tag 列表视图

## Capabilities

### New Capabilities
- `mac-local-database`: Mac 端通过 GRDB 只读连接共享 SQLite 数据库,封装数据访问层与 DATA_ROOT 配置
- `mac-media-grid-local`: Mac 端媒体网格视图基于本地数据源的实现,含分页、过滤、本地缩略图加载、QuickLook 预览

### Modified Capabilities
<!-- 无 —— 现有 specs 均针对 Vue/Android 端,Mac app 是新增端,不修改既有 capability -->

## Impact

- **代码**:`MyNote/MyNote/` 下新增 `LocalDatabase.swift`、`MediaRecord.swift`、`MediaRepository.swift`、`MediaSource.swift`、`Settings.swift`;改造 `MediaLibraryViewModel.swift` 与 `MediaLibraryView.swift`;保留但不再默认使用 `APIClient.swift`(写路径备用)
- **依赖**:Xcode SPM 新增 `groue/GRDB.swift`(~v6.x)
- **配置**:新增 `UserDefaults` key `dataRoot`(String, 用户选择的数据根目录绝对路径)
- **运行模式变化**:Mac app 不再需要 backend 进程运行;但 backend 仍是 Android 同步、Vue/Electron 旧端、以及 Mac 写操作的依赖(短期内不下线)
- **跨端约束**:Mac 端**只读** SQLite,不写 —— 避免与 Android sync 链路冲突。后续若做 Mac 写,需单独设计跨端写协调方案
- **不影响**:backend Python 代码、Android Kotlin 代码、Vue 前端、Electron wrapper、现有 SyncLog/同步协议均不改动
