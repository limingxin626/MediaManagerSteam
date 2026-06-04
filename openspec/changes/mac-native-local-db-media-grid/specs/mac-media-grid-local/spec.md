## ADDED Requirements

### Requirement: 媒体源协议抽象

App SHALL 定义 `MediaSource` 协议作为 ViewModel 与数据来源之间的契约,具体实现包括 `LocalMediaSource`(GRDB 本地)与 `APIMediaSource`(包装现有 `APIClient`,保留作为 fallback)。`MediaLibraryViewModel` 的构造函数 MUST 通过依赖注入接受 `MediaSource`,默认使用 `LocalMediaSource()`。

#### Scenario: ViewModel 默认使用本地数据源

- **WHEN** `MediaLibraryViewModel()` 无参数构造
- **THEN** 内部 `mediaSource` 是 `LocalMediaSource` 实例
- **AND** 所有分页查询走本地 SQLite,无 HTTP 流量

#### Scenario: 显式注入 APIMediaSource 用于回退

- **WHEN** 调试时构造 `MediaLibraryViewModel(mediaSource: APIMediaSource())`
- **THEN** 该实例的所有分页查询通过 HTTP 调 backend,行为等同改造前

### Requirement: 本地媒体分页游标

`LocalMediaSource.list` SHALL 使用复合游标 `"{created_at_iso}|{id}"`,排序按 `created_at DESC, id DESC`。当未传 cursor 时返回最新一页;传入 cursor 时返回严格早于该游标的下一页。每次 query MUST 取 `limit + 1` 条以判定 `has_more`。

#### Scenario: 首屏加载(无游标)

- **WHEN** `LocalMediaSource.list(cursor: nil, limit: 40, type: nil, starredOnly: false)` 被调用
- **THEN** SQL: `SELECT * FROM media ORDER BY created_at DESC, id DESC LIMIT 41`
- **AND** 若返回 41 行,丢弃最后一行,`has_more = true`,`next_cursor = "{第40行.created_at}|{第40行.id}"`
- **AND** 若返回 ≤40 行,`has_more = false`,`next_cursor = nil`

#### Scenario: 加载下一页(带游标)

- **WHEN** `LocalMediaSource.list(cursor: "2026-06-01T10:00:00|123", limit: 40, ...)` 被调用
- **THEN** SQL: `WHERE (created_at, id) < ('2026-06-01T10:00:00', 123) ORDER BY created_at DESC, id DESC LIMIT 41`
- **AND** 同样按 limit+1 规则计算 `has_more` 与 `next_cursor`

#### Scenario: 游标格式无效

- **WHEN** 传入的 cursor 字符串不符合 `"{iso}|{int}"` 格式
- **THEN** 抛出明确错误(不静默忽略),ViewModel 捕获后展示错误提示

### Requirement: 类型过滤

`LocalMediaSource.list` SHALL 支持 `type` 参数:`"image"` / `"video"` / `nil`(全部)。判定基于 `mime_type` 列前缀(`image/*` 视为图片,`video/*` 视为视频)。

#### Scenario: 仅查询图片

- **WHEN** 调用时 `type = "image"`
- **THEN** SQL 添加 `AND mime_type LIKE 'image/%'`

#### Scenario: 仅查询视频

- **WHEN** 调用时 `type = "video"`
- **THEN** SQL 添加 `AND mime_type LIKE 'video/%'`

#### Scenario: 不过滤类型

- **WHEN** 调用时 `type = nil`
- **THEN** SQL 不添加 mime_type 过滤条件

### Requirement: 收藏过滤

`LocalMediaSource.list` SHALL 支持 `starredOnly: Bool` 参数。当为 true 时只返回 `starred = 1` 的记录;false 时不过滤。

#### Scenario: 仅显示收藏

- **WHEN** 调用时 `starredOnly = true`
- **THEN** SQL 添加 `AND starred = 1`

### Requirement: 媒体网格 UI 复用现有视图

`MediaLibraryView`(SwiftUI `LazyVGrid`,4 列网格)与 `MediaLibraryViewModel` 的 UI/业务逻辑 SHALL 保持不变(除构造函数注入与图片加载替换外)。已有的"全部 / 图片 / 视频"切换按钮与星标过滤按钮 MUST 直接复用。

#### Scenario: 切换媒体类型

- **WHEN** 用户点击"图片"按钮
- **THEN** `MediaLibraryViewModel.changeMediaType("image")` 被触发
- **AND** 重新调用 `mediaSource.list(...)` 拉取第一页,媒体网格刷新

#### Scenario: 切换星标过滤

- **WHEN** 用户点击星标按钮
- **THEN** `MediaLibraryViewModel.toggleStarredOnly()` 被触发
- **AND** `showOnlyStarred` 取反,重新加载首页

#### Scenario: 无限滚动加载更多

- **WHEN** 用户滚动到接近底部,触发 `loadMore()`
- **AND** `hasMore = true` 且 `nextCursor != nil` 且 `isLoadingMore = false`
- **THEN** 用当前 `nextCursor` 调 `mediaSource.list(...)`,新结果 append 到 `media` 数组

### Requirement: 本地缩略图加载

网格 cell SHALL 通过 `LocalImageLoader` 异步加载缩略图,从 `media.localThumbURL` 读 webp 文件,解码为 `NSImage`,并按 `media.id` 缓存到 `NSCache<NSNumber, NSImage>`。MUST 不使用 `AsyncImage(url:)`(避免滚动时重复解码)。

#### Scenario: 首次显示一个 cell

- **WHEN** 一个网格 cell 进入可视区域且其 `media.id` 不在缓存中
- **THEN** `LocalImageLoader` 在后台队列读 `media.localThumbURL` 对应的 webp 文件
- **AND** 解码成功后写入 `NSCache`,主线程更新 cell

#### Scenario: 重复显示已缓存的 cell

- **WHEN** cell 重新出现且 `media.id` 已在 `NSCache` 中
- **THEN** 直接同步取出 `NSImage`,无 IO

#### Scenario: 缩略图文件缺失

- **WHEN** `media.localThumbURL` 指向的文件不存在
- **THEN** cell 显示占位图(灰色背景 + photo icon),不崩溃,不无限 spinner

### Requirement: 视频与图片详情打开

当用户点击网格中的某项时:图片 MUST 用全屏 `NSImage` 大图显示,视频 MUST 用 `AVPlayer(url: media.localFileURL)` 内嵌 `VideoPlayer` 播放。

#### Scenario: 点击图片项

- **WHEN** 用户点击一个 `mime_type` 以 `image/` 开头的 cell
- **THEN** 打开详情视图,显示 `NSImage(contentsOf: media.localFileURL)` 大图
- **AND** 提供关闭按钮或 ESC 键关闭

#### Scenario: 点击视频项

- **WHEN** 用户点击一个 `mime_type` 以 `video/` 开头的 cell
- **THEN** 打开详情视图,使用 SwiftUI `VideoPlayer(player: AVPlayer(url: media.localFileURL))` 内嵌播放
- **AND** 提供关闭按钮或 ESC 键关闭

### Requirement: QuickLook 空格预览

网格视图 SHALL 支持选中一个 cell 后按空格键弹出 `QLPreviewPanel` 预览本地媒体文件(图片或视频)。再次按空格或 ESC 关闭。

#### Scenario: 选中并按空格

- **WHEN** 用户点击一个 cell(进入 selected 状态)然后按空格键
- **THEN** `QLPreviewPanel.shared()` 显示该 media 的 `localFileURL` 内容

#### Scenario: 在 QuickLook 中切换上下张

- **WHEN** QuickLook 面板打开时,用户按方向键
- **THEN** 预览切换到网格中相邻的 media

### Requirement: 移除 Message Feed 入口

第一期 SHALL 把 `FeedView` / `FeedViewModel` 从 Xcode target 移除(或从 `ContentView` 的导航中下线)。`ContentView` MUST 只展示媒体网格,不展示空白或报错的 Message tab。

#### Scenario: app 启动后的主界面

- **WHEN** 用户启动 app 并通过 DATA_ROOT 校验
- **THEN** 主界面是 `MediaLibraryView`,无 Message tab、无 Actor tab
