## 1. 数据层:MessageRecord / MessageRepository

- [x] 1.1 新建 `MyNote/MyNote/MessageRecord.swift`,定义 `MessageRecord` / `MessageMediaRecord` / `ActorRecord` / `TagRecord` 四个 GRDB `FetchableRecord` + `TableRecord`,字段名用 snake_case `CodingKeys` 映射到 backend `app/models/__init__.py` 实际列名(对齐 `MediaRecord` 风格)
- [x] 1.2 在同一文件加 `toUIModel()`:`MessageRecord.toUIModel(actor: ActorRecord?, mediaItems: [MessageMediaItem], tags: [MessageTag]) -> Message`,沿用 ISO formatter 序列化 `createdAt` / `updatedAt`,`starred = (starred != 0)`
- [x] 1.3 新建 `MyNote/MyNote/MessageRepository.swift`,提供 `list(cursor, limit, actorId, tagId, issueId, queryText, mediaId, starredOnly) async throws -> (items, nextCursor, hasMore)`,SQL builder 与 backend `message.py::_build_message_query` 过滤参数一致(actorId 0 → IS NULL,tagId 走「message_tag ∪ media_tag」并集,mediaId 走 `message_media` 子查询,等等)
- [x] 1.4 `MessageRepository.monthlyDayCount(year, month, filters) -> [DayCount]`:返回该月有消息的日期 + count,filters 与 `list` 复用同一组 SQL builder,保证 timeline 计数与 feed 命中数一致
- [x] 1.5 `MessageRepository.fetchMessageDetail(id) async throws -> Message?`:取单条 message 完整数据(actor + media_items + tags),与 `list` 共用批量预取逻辑,供 detail 面板点击消息时拉取
- [x] 1.6 `MessageRepository.fetchFilters() async throws -> (tags: [Tag], actors: [Actor], issues: [Issue])`:取三组过滤条目,按消息数降序(actor / tag),issue 默认 `status = 'doing'`,与 vue 端 `?status=doing` 对齐
- [x] 1.7 `MessageCursor` 私有 enum:解析 / 编码 `created_at` ISO 字符串,失败抛 `RepositoryError.invalidCursor`;cursor 校验在仓库入口完成,不让坏 cursor 进 SQL
- [x] 1.8 单元 SQL 验证(用 sample DB 或打印):首屏 / 续翻 / actor 0 / tag 联合 / mediaId 子查询 / queryText LIKE / starredOnly 各跑一次,行数与 backend 一致

## 2. UI 模型与本地 URL 扩展

- [x] 2.1 改 `MyNote/MyNote/Models.swift`:把现有 `Message` / `MessageMediaItem` 重组为「`Message` UI struct(持有 `mediaItems: [MessageMediaItem]` + `tags: [MessageTag]`)+ `MessageMediaItem` UI struct(持有 ISO 字符串 + `tags: [MessageTag]`)」,字段不变;`MessageTag` 不动
- [x] 2.2 给 `MessageMediaItem` 加扩展 `var localThumbURL: URL?`、`var localFileURL: URL?`,实现与 `Media.localThumbURL` / `Media.localFileURL` 一致(Settings.dataRoot + 路径拼接 + RepositoryManager 解析)
- [x] 2.3 新增 `Actor` UI struct(`MyNote/MyNote/Models.swift` 末尾追加,与 Message 同文件):`id: Int, name: String, avatarPath: String?, messageCount: Int`;扩展 `var localAvatarURL: URL?` 指向 `{DATA_ROOT}/data/actor_cover/{id}.webp`
- [x] 2.4 `MessageMediaItem` 内的 media 字段直接构造为 `Media` 后再读 `localThumbURL` / `localFileURL`;如果构造点不方便,加一个 `MessageMediaItem.asMediaRecord() -> Media` 转换函数,内部填 filePath / mimeType / starred / videoMediaId 等字段

## 3. LocalImageLoader 加 actor 头像 namespace

- [x] 3.1 改 `MyNote/MyNote/LocalImageLoader.swift`:NSCache 的 key 由 `NSNumber(id)` 改为 `String("\(kind.rawValue)-\(id)")`,其中 `ImageKind` 枚举 `.mediaThumbnail` / `.actorAvatar`
- [x] 3.2 新增 `LocalImageLoader.loadActorAvatar(actorId: Int) async -> NSImage?` 平行方法,内部从 `URL(fileURLWithPath: "{DATA_ROOT}/data/actor_cover/{actorId}.webp")` 读 → webp 解码 → 写 NSCache,失败返回 nil
- [x] 3.3 保留 `loadMediaThumbnail(mediaId: Int) async -> NSImage?` 现有签名 / 行为,内部用 `.mediaThumbnail` 命名空间;`LocalThumbView` 调用方不需改
- [x] 3.4 在 `LocalImageLoader` 文件顶部注释里写明:actor 与 media 共用 NSCache 但靠 `ImageKind` 隔离 key;`NSCache<NSString, NSImage>` 而不是 `NSNumber`

## 4. ContentView 接 ZStack 模式

- [x] 4.1 改 `MyNote/MyNote/ContentView.swift`:增加 `@StateObject private var messagesViewModel = MessagesViewModel()`;`detailContent` 改为 `ZStack { HomePlaceholderView(); MessagesView(viewModel: messagesViewModel); MediaLibraryView(viewModel: mediaLibraryViewModel) }`,用 `.opacity(selectedTab == .case ? 1 : 0)` + `.allowsHitTesting(...)` 控制可见性(沿用 mac-media-page-state-and-styling 决策)
- [x] 4.2 验证 ZStack 不影响 sidebar / 选中 tab 行为;若已有 mac-media-page-state-and-styling 的 ZStack 改动就位,本任务仅做 `messagesViewModel` 注入 + `case .messages` 切换

## 5. MessagesViewModel

- [x] 5.1 新建 `MyNote/MyNote/MessagesViewModel.swift`,`@MainActor class MessagesViewModel: ObservableObject`,持有 `messages: [Message]`、`selectedMessage: MessageDetail?`、`isLoading`、`errorMessage`、`searchText`、`starredOnly`、`selectedTagId/selectedActorId/selectedIssueId`、`nextCursor`、`hasMore`、`scrollTop`、`monthlyDayCount: [DayCount]`
- [x] 5.2 `loadInitialIfNeeded()` 守门(首次 onAppear 触发,后续不重置),与 `MediaLibraryViewModel.loadInitialIfNeeded` 同结构
- [x] 5.3 `loadInitial() async`:清状态 → `repository.list(cursor: nil, limit: 20, filters)` → 拼到 `messages` 数组 → 设 `nextCursor` / `hasMore`;`scrollToBottom()`
- [x] 5.4 `loadMore() async`:仅在 `scrollTop < 200pt && hasMore && !isLoading` 时触发,`repository.list(cursor: nextCursor, limit: 20, filters)`,把返回数组 `.reverse()` 后拼到 `messages` 头部(保持时间倒序)
- [x] 5.5 `loadFilters() async`:并发 fetch tags / actors / issues,写进 `availableTags` / `availableActors` / `availableIssues`(可选,`@Published`)
- [x] 5.6 `loadMonthlyTimeline() async`:根据 `selectedTagId/selectedActorId/selectedIssueId/searchText/starredOnly` 复用 SQL 过滤参数,`repository.monthlyDayCount(...)` 写进 `monthlyDayCount`
- [x] 5.7 `selectMessage(id) async`:从 `messages` 数组里找 → `repository.fetchMessageDetail(id)` 拿完整 detail(actor / mediaItems / tags)→ 写 `selectedMessage`
- [x] 5.8 `selectFilter(kind, id) async`:三选一互斥(选 tag 清 actor/issue,反之亦然),触发 `loadInitial()`(或带 scroll-position-restore 的 `loadInitial`-like)
- [x] 5.9 `scrollToDate(date) async`:把日期对应 ISO 字符串作为 cursor 调 `repository.list`,渲染后滚到该日首条消息位置
- [x] 5.10 `debouncedSearch()`:300ms debounce 触发 `loadInitial()`,使用 `Task` + `Task.sleep` 实现(参考 vue 端 `onSearch` 写法)
- [x] 5.11 写 `changeStarred` / `delete` / `merge` / `split` 等方法时**故意不写**,用注释明确「Mac 端 read-only,写操作走 backend HTTP,后续 change 单独引入」

## 6. MessagesView 主视图骨架

- [x] 6.1 新建 `MyNote/MyNote/MessagesView.swift`,`struct MessagesView: View { @ObservedObject var viewModel: MessagesViewModel }`;整体 `HStack(spacing: 0) { filterSidebar; messagesPane; (optional) detailPane }`
- [x] 6.2 `NavigationStack` 包整个 HStack,detail 面板里的媒体网格点击推 `MediaPreviewDestination` 进入 `MediaDetailView` 复用;在打开预览时设 `PreviewTitle.shared.title`
- [x] 6.3 顶栏 `MessagesTopBar`:标题「消息」+ 搜索框(`.searchable` 或 `TextField`)+ 收藏 toggle + 刷新按钮 + DateScrubber(条件渲染,timeline 非空时显示)
- [x] 6.4 底部条(空实现,read-only 阶段不显示输入框;留位但不渲染),与 vue 端 `MessageComposeInline` 位置一致
- [x] 6.5 `.onAppear`:`Task { await viewModel.loadInitialIfNeeded() }`、`.task(id: viewModel.scrollTop) { ... }` 用于向上滚到底部时 `loadMore`
- [x] 6.6 `.toolbar` 与媒体页同款:不放 Picker,只放 `RefreshButton`(可选);系统标题栏显示「消息」(`navigationTitle(AppTab.messages.title)`)

## 7. 消息流 Feed 与消息卡

- [x] 7.1 `MessagesList`(`ScrollView { LazyVStack(spacing: 12) { ... } }`):`ForEach(viewModel.messages)` 渲染 `MessageCard`;`.id(\.id)` 强制 cell 标识稳定
- [x] 7.2 `MessageCard`(`MyNote/MyNote/MessageCard.swift`,新文件):顶部条(actor avatar + name + 相对时间)、正文(`Text` + 简单 `Link` 检测)、tag chips(`HStack` 平铺)、媒体网格(`MessageMediaGrid`)、底部条(星标只读 `Image` + 媒体数 + ID)
- [x] 7.3 `MessageMediaGrid`(`MyNote/MyNote/MessageMediaGrid.swift`,新文件):根据 `items.count` 选 layout —— 1 张 1x1 大图,2 张 1x2,3-9 张 3x3 平铺,>9 张前 9 张 + 1 个「+N」占位;每张 cell 用 `LocalThumbView(media: item.asMedia())` 渲染
- [x] 7.4 媒体 cell 的点击回调 `onMediaClick(index: Int)`,`MessagesView` 收到后用 `selectMessage` + 推 `MediaPreviewDestination`;不直接进 preview(先开 detail,detail 里再点媒体才进 preview)
- [x] 7.5 卡片 hover 高亮:用 `@State private var isHovered: Bool` + `.onHover { isHovered = $0 }` 切换背景色;星标按钮 hover 时显式,默认半透明
- [x] 7.6 `RelativeTimeFormatter` 小工具:输入 ISO 字符串输出「2 小时前」「昨天」「3 天前」「2026-05-29」,放 `MyNote/MyNote/RelativeTimeFormatter.swift`,纯函数

## 8. 消息详情面板

- [x] 8.1 `MessageDetailPane`(`MyNote/MyNote/MessageDetailPane.swift`,新文件):当 `viewModel.selectedMessage != nil` 时显示
- [x] 8.2 顶部条:「消息详情」+ 创建时间(绝对日期) + 「× 关闭」按钮(调 `viewModel.selectedMessage = nil`)
- [x] 8.3 正文:完整 text + tag chips(同 `MessageCard` 的渲染,这里再渲染一次)
- [x] 8.4 媒体网格:复用 `MessageMediaGrid`,但每个 cell 的 onClick 直接推 `MediaPreviewDestination`(因为 detail 里的媒体点击就是预览,不再绕一层)
- [x] 8.5 ESC / × 关闭 detail:用 `.onKeyPress(.escape) { viewModel.selectedMessage = nil; return .handled }` 或 `.keyboardShortcut(.cancelAction)` 绑定 ESC
- [x] 8.6 宽度 < 800pt 时 detail 不显示(强制 feed 占满),在 `MessagesView` 用 `GeometryReader` 测量后 `if width >= 800` 分支控制

## 9. 左侧 FilterSidebar

- [x] 9.1 `FilterSidebar`(`MyNote/MyNote/FilterSidebar.swift`,新文件):`List` 风格,3 个 `Section` —— 标签 / 演员 / Issue
- [x] 9.2 tag 列表:从 `viewModel.availableTags` 渲染,选中态走 `List(selection: $viewModel.selectedTagId)`,section 顺序为 Tag → Actor → Issue
- [x] 9.3 actor 列表:第 1 项「无演员」(`actorId == 0` 占位,显示「无演员」),其余按 messageCount 降序
- [x] 9.4 issue 列表:第 1 项「无 issue」(`issueId == 0`),其余按 createdAt 降序
- [x] 9.5 选中条目 → 调 `viewModel.selectFilter(.tag, id)` / `.actor` / `.issue`,viewmodel 内部互斥;List 自身用单选 binding
- [x] 9.6 顶栏加「清除过滤」徽章:有任一 filter 选中时显示,点 × 清空全部(等价于 `selectFilter(kind, nil)`)
- [x] 9.7 窗口宽度 < 800pt 时 FilterSidebar 折叠为 toolbar dropdown(`Menu` + `Picker`),沿用 macOS 风格;不展开侧栏挤掉内容

## 10. 顶栏 DateScrubber(消息域)

- [x] 10.1 `DateScrubber` 已存在,直接复用 `MyNote/MyNote/DateScrubber.swift`;`MessagesView` 顶栏 toolbar 区域 `if !viewModel.monthlyDayCount.isEmpty { DateScrubber(timeline: viewModel.monthlyDayCount, ...) }`
- [x] 10.2 `DateScrubber` 当前的 `TimelineEntry` 期望 `(year, month, day, count)`,与 `MessageRepository.monthlyDayCount` 返回结构一致;`currentDate` 由当前 `viewModel.scrollTop` 落在哪条消息反推
- [x] 10.3 `onJump` / `onJumpFinal` 调 `viewModel.scrollToDate(date)`,VM 内部用 cursor 重拉 + 滚动定位

## 11. 状态保留 / 切 tab 不丢

- [x] 11.1 `ContentView` 持有 `@StateObject private var messagesViewModel`(已由 4.1 完成),`MessagesView` 用 `@ObservedObject` 注入
- [x] 11.2 `MessagesViewModel.loadInitialIfNeeded` 守门,`hasLoadedOnce` 单次开关(同 `MediaLibraryViewModel`)
- [x] 11.3 `MessagesView` 的 `ScrollView` 把 `scrollTop` 同步回 VM(`PreferenceKey` + `GeometryReader` 或 `ScrollView`'s `.onScrollGeometryChange(for:of:action:)`(macOS 14+));验证切到「媒体」再切回,`scrollTop` 数值恢复,UI 滚到原位
- [x] 11.4 `MessagesViewModel.selectedMessage` 是 `@Published`,切回 tab 时 view 自动重建 detail pane

## 12. 空状态 / 错误 / 加载态

- [x] 12.1 `MessagesView` 顶层 `ZStack` 渲染:feed 之上叠加 `if isLoading && messages.isEmpty { ProgressView() }` 居中
- [x] 12.2 `if !isLoading && messages.isEmpty && errorMessage == nil` 时显示「暂无消息」空状态(`Image` + 「暂无消息」副标题)
- [x] 12.3 顶部浮层 `errorMessage`,带 × 关闭按钮(沿用 `MediaLibraryView.errorMessage` 模式)
- [x] 12.4 首次 refetch 完成时(scrollToBottom 前)不显示「暂无消息」,因为 `messages` 数组临时为空会闪空状态;用 `isLoading` 守门避免闪烁

## 13. LocalImageLoader 联调 + 联测

- [ ] 13.1 用 sample DB 启动 app,切到「消息」tab,验证首屏渲染 20 条消息,媒体缩略图正常显示,actor 头像缺失时显示 `person.circle` 占位
- [ ] 13.2 测过滤:点 tag「#旅行」→ feed 重渲染;切「仅看收藏」→ feed 过滤;搜索「hello」→ feed 过滤
- [ ] 13.3 测日期跳转:DateScrubber 拖到 2026-05-29,释放后 feed 滚到该日首条消息
- [ ] 13.4 测详情面板:点消息卡 → 右侧 detail 滑入,显示完整内容;点 detail 里的媒体 → 进入 `MediaDetailView` 预览;ESC / × 关闭 detail
- [ ] 13.5 测切 tab 保留:滚到 50% 位置 + 选中 message → 切到「媒体」→ 切回「消息」,状态完全恢复
- [ ] 13.6 测写操作为空:消息卡 hover 显示的星标按钮为 disabled 态;detail 面板不显示「编辑」「删除」按钮
- [ ] 13.7 测 GRDB 失败场景:在 `MessageRepository.list` 临时抛 `RepositoryError.databaseNotOpen`,验证 `errorMessage` 浮层 + 刷新按钮可重试
- [ ] 13.8 测与 `LocalImageLoader` 命名空间不冲突:同时打开媒体页(看媒体缩略图)与消息页(看演员头像),NSCache 不互相覆盖

## 14. macOS 风格细节(沿用 mac-media-page-state-and-styling 决策)

- [x] 14.1 `MessagesView` 滚动条:`ScrollView` 在 macOS 上默认是有滚动条的(行为与媒体页 NSScrollView 不同);本期不强制隐藏,保持系统默认,与「消息」tab 的轻量定位匹配
- [x] 14.2 系统标题栏:`navigationTitle(AppTab.messages.title)`(沿用 `MediaLibraryView.navigationTitle(...)` 模式)
- [x] 14.3 深色模式:`Color(.windowBackgroundColor)` / `Color(.controlBackgroundColor)` 等系统色,跟随系统设置切换
- [x] 14.4 字体:`.font(.body)` 消息正文、`.font(.caption)` 时间戳、`.font(.headline)` actor 名字,与 mac 端系统字体一致

## 15. 文件清单 & Xcode target

- [x] 15.1 新增 4 个文件:`MessagesView.swift` / `MessagesViewModel.swift` / `MessageRepository.swift` / `MessageRecord.swift`
- [x] 15.2 新增 3 个 UI 组件文件:`MessageCard.swift` / `MessageMediaGrid.swift` / `MessageDetailPane.swift` / `FilterSidebar.swift` / `RelativeTimeFormatter.swift`(共 5 个,前面写「3 个」是漏数,实际 5 个)
- [x] 15.3 删除 `MyNote/MyNote/FeedView.swift` 与 `FeedViewModel.swift`(早期 stub,本次重写不需要);删除 `MessagesPlaceholderView.swift`(被 MessagesView 替代)
- [x] 15.4 修改:`MyNote/MyNote/ContentView.swift`、`Models.swift`、`LocalImageLoader.swift`
- [x] 15.5 在 Xcode 中确认新文件已加入 `MyNote` target(`MyNote/MAC_TODO.md` 第 1.3 步的统一流程;若 `PBXFileSystemSynchronizedRootGroup` 已生效,放对目录就自动进 target)
- [x] 15.6 编译通过,启动 app,Messages tab 渲染无报错

## 16. 开发日志

- [x] 16.1 在项目根目录的开发日志中追加本次变更(每天一篇日志的规则),记录:Mac 端「消息」tab 从占位页升级为完整消息流,与 vue 端 Message.vue 只读子集同构;新增 9 个 Swift 文件,删除 3 个旧文件
