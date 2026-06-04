## Context

当前 Mac app(`MyNote/MyNote/`)是 SwiftUI 壳 + `APIClient` 调用 `http://127.0.0.1:8002` 的 Python backend,跟 Vue/Electron 共用一套 HTTP API。已有的实现包括 `MediaLibraryView`(`LazyVGrid` + 4 列网格 + 类型/收藏过滤)、`MediaLibraryViewModel`(分页 + 加载更多)、`Models.swift`(Media/Message/Tag 结构体,字段与 backend Pydantic schemas 对齐)。

项目定位变化:Mac 是主力,Android 是辅助,Web/Electron 不再演进。Backend 仍存在,但只是 Android 同步与历史端兼容用,不再是 Mac 的运行依赖。

数据库 schema 由 `backend/app/models/__init__.py` 定义(`Message`/`Actor`/`Tag`/`Media`/`MessageMedia` 等),通过 SQLAlchemy 写入到 `DATA_ROOT/db.sqlite3`。同一文件 + 同目录布局(`data/thumbs/{id}.webp`、`uploads/YYYY/MM/DD/`)可被任何 SQLite 客户端直读。

## Goals / Non-Goals

**Goals:**
- Mac app 第一期可以**完全脱离 backend 进程**运行,只要 `DATA_ROOT` 指向一份有效的数据库与媒体目录
- 媒体网格视图(`MediaLibraryView`)展示、滚动加载、类型/收藏过滤全部走本地 SQLite
- 缩略图、视频、原图都从本地文件系统加载,无 HTTP 流量
- 切换数据源(本地 vs HTTP)只改一行构造代码,便于回退验证
- 保留 schema 与 backend 一致 —— Android、backend 继续按原方式工作

**Non-Goals:**
- 不做任何写操作(starred toggle / 上传 / 删除等)。UI 上隐藏写入入口
- 不做多设备同步,不接 iCloud Drive / Syncthing 适配层
- 不做 `Message` feed、`Actor` 列表、`Tag` 管理视图
- 不做 ffmpeg / Blake2b / hashtag 解析等媒体处理 pipeline
- 不做 Spotlight 索引、Share 扩展、Photos 框架导入(后续阶段)
- 不实现 Mac 端独立 sync server 或 schema migration runner

## Decisions

### Decision 1: 用 GRDB.swift,不用 SwiftData / Core Data

**选择**:Xcode SPM 引入 `groue/GRDB.swift`(v6.x),手动定义 `MediaRecord: FetchableRecord, TableRecord`。

**理由**:
- SwiftData / Core Data 会在表里加隐藏字段(`Z_PK`/`Z_ENT`/`Z_OPT`),完全无法对齐 backend SQLAlchemy 生成的扁平 schema
- GRDB 是 SQLite 的薄封装,列名、类型完全可控,可以一一对齐 `backend/app/models/__init__.py:82` 的 `Media` 表
- GRDB 支持只读模式 + 编译期类型检查 + 同步/异步两种 API,生态成熟

**替代方案**:
- SwiftData → 否决,schema 不可控
- 直接用 C 层 `sqlite3` API → 否决,样板代码太多
- FMDB → 否决,API 老旧,不如 GRDB 现代

### Decision 2: 只读连接 + `readonly = true`

**选择**:`DatabaseQueue` 打开时设 `Configuration.readonly = true`,禁止任何写入。

**理由**:
- 第一期 Mac 不写,避免 schema migration、UNIQUE 约束、SyncLog 触发器等复杂性
- 防止意外写入污染 backend / Android 的数据
- 只读模式不会创建 `-wal` / `-shm` 副本文件(WAL 模式才需要),对未来跨设备同步的副作用最小

**风险**:如果 backend 此时正以 WAL 模式写入同一个文件,只读连接可能读到稍旧的 snapshot。LAN 单用户场景可接受,UI 下拉刷新即可拿到最新。

### Decision 3: 分页游标用 `(created_at, id)` 而非 backend 的 `(created_at, position)`

**选择**:本地 `MediaRepository.list()` 用 `WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT N+1`。

**理由**:
- backend `/media` 接口的复合游标 `{created_at}|{position}` 中的 `position` 来自 `MessageMedia` junction —— 因为该接口按"媒体在 message 中的位置"排序
- Mac 第一期查的是**裸 `Media` 表**(不 join `MessageMedia`),没有 position 字段,改用 `id` 兜底
- 同 `created_at` 多条记录用 `id` DESC 稳定排序,游标唯一性可保证

**Trade-off**:本地版与 backend 接口语义不严格等价。若用户在某条 message 内调整了媒体顺序,本地视图不反映该顺序。对"媒体库网格"这个 use case 影响可忽略——网格按时间倒序即可,顺序细节属于 message 详情语义。

### Decision 4: `MediaSource` 协议抽象,本地为默认

**选择**:

```swift
protocol MediaSource {
    func list(cursor: String?, limit: Int, type: String?, starredOnly: Bool) async throws -> MediaCursorResponse
}

final class LocalMediaSource: MediaSource { ... }  // GRDB 实现
final class APIMediaSource: MediaSource { ... }    // 包装现有 APIClient
```

`MediaLibraryViewModel` 构造函数接受 `MediaSource`,默认 `LocalMediaSource()`。

**理由**:
- 完全不动 `MediaLibraryView` 的 UI 代码与 `MediaLibraryViewModel` 的业务逻辑
- 切换数据源用于"backend 临时不在 / 调试本地查询"两种场景,零代价
- 未来若引入第三种数据源(如缓存层、Mock for tests)同协议扩展

**替代方案**:
- 直接把 `APIClient` 重命名为 `MediaRepository` 并改实现 → 否决,失去回退能力
- 用 enum 而非 protocol → 否决,扩展性差

### Decision 5: DATA_ROOT 用户配置 + 启动时校验

**选择**:
- `Settings.swift` 暴露 `dataRoot: URL?`,持久化到 `UserDefaults` key `dataRoot`
- 首次启动若未配置,显示一个引导界面:按钮触发 `NSOpenPanel.runModal()` 让用户选目录
- 启动时校验:`dataRoot/db.sqlite3` 存在 + 可读 + `SELECT 1 FROM media LIMIT 1` 成功;失败显示重新选择按钮
- 缩略图路径: `dataRoot/data/thumbs/{id}.webp`;媒体文件路径:`dataRoot/{media.file_path}`(因为 `file_path` 在 backend 里存的是相对 `DATA_ROOT` 的相对路径,如 `uploads/2026/06/04/xxx.mp4`)

**理由**:
- 用户机器上的数据目录路径不可预测(可能是本地、SMB 挂载、外置盘),不能硬编码
- 用 `NSOpenPanel` 而非文本框,顺便拿到 sandbox 文件访问授权(若未来上 MAS,可换成 security-scoped bookmark)

### Decision 6: 缩略图加载用 `NSImage` + 内存缓存,不用 `AsyncImage`

**选择**:封装 `LocalImageLoader`,内部用 `NSCache<NSNumber, NSImage>` 按 `media.id` 缓存解码后的 `NSImage`。网格 cell 异步加载并 `weak` 持有。

**理由**:
- `AsyncImage` 设计给 HTTP 用,本地文件每次滚动会反复解码 webp,大网格滚动卡顿
- `NSImage(contentsOf: fileURL)` 是同步 IO,放后台队列即可;`NSCache` 自动控内存
- webp 解码 macOS 14+ 系统原生支持(`NSImage` 直接吃),不用第三方库

**风险**:webp 在更老版本 macOS 上需要 `SDWebImageWebPCoder` 之类。`MyNote.entitlements` 看 deployment target,若 ≥13 即可原生。

### Decision 7: 删除 `FeedView` 而非保留

**选择**:第一期把 `FeedView.swift` / `FeedViewModel.swift` 从 target 移除(文件可保留在磁盘做参考)。

**理由**:
- 这两个文件目前依赖 `APIClient.getMessages()`,本地化它们超出本期范围
- 留着会让 `ContentView` 的导航栏出现一个永远 404 / 报错的入口,体验差
- 后续做 Message feed 时再加回来,届时同样走 `MessageSource` 协议

## Risks / Trade-offs

- **[Risk] WAL 模式下读到旧 snapshot**:backend 写入时 Mac 只读连接可能看到稍旧数据 → **Mitigation**:UI 提供下拉刷新;LAN 单用户场景延迟可接受;后续可加 `pragma wal_checkpoint(PASSIVE)` 触发
- **[Risk] 用户选错 DATA_ROOT**:目录里没有 `db.sqlite3` 或 schema 不匹配 → **Mitigation**:启动校验 + 错误提示 + 重新选择按钮;`MediaRecord` 字段不匹配时 GRDB 会抛具体列名,展示给用户
- **[Risk] webp 解码兼容**:老 macOS 不支持 → **Mitigation**:Xcode 工程设 deployment target ≥ macOS 14;若必须支持更老,后续引 `SDWebImageWebPCoder`
- **[Risk] schema 漂移**:backend 后续改 schema 后 Mac 没同步更新 → **Mitigation**:本期接受手动同步;后续可在启动时跑 `PRAGMA table_info(media)` 与 Swift 端期望列对比,不匹配则警告
- **[Risk] 大库性能**:几十万条 Media 时 `ORDER BY created_at DESC` 是否有索引? → backend 已有 `index=True` on `Media.created_at`,本地直接复用,实测应无问题;若慢可加复合索引 `(created_at, id)`
- **[Trade-off] 写路径仍走 HTTP**:starred 切换等操作短期内需 backend 在线;但第一期 UI 上隐藏这些入口,用户感知不到。等做写阶段再统一规划

## Migration Plan

**部署**:
1. 用户拉新版 Mac app,首次启动弹出 DATA_ROOT 选择
2. 用户选指向 backend 数据目录(同机 → 本地路径;异机 → SMB 挂载点)
3. 校验通过即进入媒体网格,无需启动 backend 进程

**回退**:
- 把 `MediaLibraryViewModel` 默认数据源从 `LocalMediaSource()` 改回 `APIMediaSource()`,重新打包即可
- 或者在 Settings 加一个 "use legacy HTTP backend" 开关(若用户反馈本地有问题)

**与现有端的兼容**:
- backend / Android / Vue / Electron 零改动
- Mac 只读,不会破坏 backend 的 SyncLog 或 Android 的 sync 状态

## Open Questions

1. **Deployment target**:Xcode 工程现在的 macOS minimum 是多少?需要确认能否依赖 `NSImage` 原生 webp 解码(≥13/14 即可)
2. **首次启动 onboarding 文案**:是否需要给用户解释"为什么要选目录"?还是简单"请选择 MediaManager 数据目录"足够?(本期按后者实现,可后续打磨)
3. **是否要在 Settings 里允许切换 LocalMediaSource / APIMediaSource**:让用户/开发者手动切?还是只在代码里写死本地优先?(本期建议只在代码里切,Settings 不暴露,避免 UI 复杂度)
