## Context

Mac 端 `MyNote` 是项目的当前主推端,`MyNote/MAC_TODO.md` 把「消息 Feed」列为第一期外的二期任务。Vue 端 `vue/src/views/Message.vue` 已经成型:左 feed + 右 detail + 左侧 `FilterSidebar`(tag/actor/issue)+ 顶栏搜索/星标/合并/刷新 + 内嵌日历(v-calendar)做日期跳转 + 内嵌 `MediaPreview` 做全屏预览 + `MessageComposeInline` 做底部输入。Mac 端只读 SQLite(GRDB 只读 DatabaseQueue),backend 走 `vue → FastAPI → SQLite` 协议。`Models.swift` 里已有 `Message` / `MessageMediaItem` / `MessageTag` 三个结构体,但它们是面向 HTTP API 反序列化的(目前没有任何地方使用),不是 DB record 也不是 UI model。

本 change 把 Vue 端「消息流」的**只读**子集搬到 Mac 端:**feed 列表 + 详情面板 + 过滤 + 日期跳转 + 媒体预览**。**不**做创建/编辑/删除/合并/拆分/上传 —— 写操作继续走 backend HTTP,与「read-only first phase」基调一致。`FeedView.swift` / `FeedViewModel.swift` 是早期 stub,目前不在 target(`MyNote/MAC_TODO.md` 1.4 节),这次直接重写,旧的 stub 不复用。

## Goals / Non-Goals

**Goals:**
- Mac 端「消息」tab 实现与 vue 端 Message.vue 同构的只读浏览能力(feed + detail + 过滤 + 日期跳转 + 媒体预览)
- 数据层走 GRDB 直读 `message` / `message_media` / `message_tag` / `media_tag` / `tag` / `actor` 六张表,不依赖 backend 运行
- 标签/演员/Issue 侧栏过滤 + 全文搜索 + 仅看收藏(filter 组合与 vue 端 1:1 对齐)
- 消息卡 + 内嵌媒体网格复用 mac 端 `LocalThumbView` + 现有 `LocalImageLoader`(不重新做图片解码)
- 媒体点击预览直接复用 `MediaDetailView`(已经支持本地文件 URL)
- 切到「主页」/「媒体」再切回「消息」,消息流保留滚动位置 + 当前选中消息 + 过滤条件(沿用 mac-media-page-state-and-styling 的 ContentView ZStack 方案)
- SQL 与 backend `/messages/with-detail` 路由的过滤参数语义一致(便于将来后端与 Mac 端共享 QA 脚本)

**Non-Goals:**
- 消息的创建 / 编辑 / 删除 / 合并 / 拆分 / 上传 —— 写操作走 backend HTTP
- Issue 创建、actor 创建 —— 本期不实现
- 消息文本的 markdown 渲染样式打磨(本期用 `.font(.body)` 直接显示纯文本,带 `link`/换行/基本段落)
- 媒体星标/删除/旋转/标签编辑 —— 走 backend(媒体页 MediaDetailView 内的写操作同理,本 change 不动)
- 消息搜索高亮、@mention 解析
- 通知(无后端推送)、未读标记
- 多选合并(merge mode)、拆分模式(split mode)—— 写操作,本期不实现
- Vue 端 `IssuePinnedBanner` 的「Pinned issue 顶部条」UI —— 本期侧栏只读 issue 列表,不复制 banner
- macOS 视觉风格打磨(mac-media-page-state-and-styling 风格的 focus ring / 滚动条 / ZStack 持 view 等) —— 复用其结论,但不再单独开 follow-up

## Decisions

### Decision 1: 消息分页用 ISO 简单游标,不复用媒体桶模型

**选择**: cursor = `created_at` ISO 字符串(`yyyy-MM-dd'T'HH:mm:ss.SSSSSS`),降序,带 `id` 兜底。MessageRepository 提供 `list(cursor, limit, filters) -> (items, nextCursor, hasMore)`,**不**用 `MediaRepository` 那套「按 (year, month, day) 分桶」+ 「loadBucket(afterCursor)」模型。

**理由**:
- 消息数据量比媒体小一个数量级(典型个人库 100~1000 条消息,媒体上万),简单 `LazyVStack` + ISO 游标分页够用,引入桶模型是过度设计
- vue 端 Message.vue 的「按日期分隔」「日历跳到某日」是**渲染层**做的(date separator + 当前可见日期 badge),**数据层**是 ISO 游标,Mac 端同构
- 沿用后端 `/messages/with-detail` 路由的 cursor 协议(MAC 是 read-only 直读,SQL 自己手写,后端的 cursor 解析逻辑只做参考)

**取舍**:
- 用户快速滚到几千条以后才可能感知到 ISO 游标的劣势(每次 limit 条)。当前规模下不构成问题
- 滚到中段时 backfill 行为与 vue 端一致(向上滚触发「加载更早」,向下滚触发「加载更新」),靠两个 cursor 独立管理

**备选方案否决**:
- 复用 `MediaRepository.timeline` / `loadBucket` 模型:消息没有 timeline 索引快路径,而且消息文本的「按日桶」语义对消息来说颗粒太细(用户期望一次看一串)
- `Int64` 单一游标(created_at 序列化为 microsecond):GRDB 排序性能更好,但与 vue 端 / 后端契约不一致,会引入 Mac 端独有的协议

### Decision 2: 视图结构 = `MessagesView { HStack { MessagesList | (optional) MessageDetailPanel } }`,不嵌 `NavigationSplitView`

**选择**: 整体仍是 `ContentView → NavigationSplitView { SidebarView | detail }`,detail 区域里 `MessagesView` 用 `HStack` 左 feed + 右 detail;detail 不出现时,feed 占满宽度;detail 出现时 feed 占 ~50%,detail 占 ~50%。

**理由**:
- 「feed 占满 vs 50/50」是同一窗口内的布局切换,不是 sidebar/detail 的二栏 —— 用 `NavigationSplitView` 套两层会把视觉搞成「三层」,且 macOS 没有「detail 里的第二个 split」范式
- vue 端 Message.vue 走「CSS flex w-1/2 / flex-1」也是同一窗口内切,Mac 端同构
- 不出现 detail 时由 `selectedMessage == nil` 触发,feed 自动占满;不需要额外动画

**取舍**:
- 切回 feed 满宽时 detail 视图销毁(再点又新建),与 vue 端 behavior 一致
- 宽度小于 800pt 时强制 feed 满宽(临时实现:用 `GeometryReader` 测量 + `if width > 800` 分支),与 mac 端整体「大屏为主」定位一致

**备选方案否决**:
- 用 `NavigationSplitView` 二级嵌套:macOS 上视觉很怪,且 SwiftUI 在嵌套 split 上的侧栏/工具栏优先级混乱
- 用 sheet 弹出 detail:vue 端也是右侧分栏(只是 CSS 实现的),改成 sheet 反而与原设计偏离

### Decision 3: feed 渲染用 `LazyVStack` + ID,不用 `List` 也不用自己造虚拟滚动

**选择**: feed 用 `ScrollView { LazyVStack(spacing: 12) { ForEach(messages) { MessageCard } } }`,靠 SwiftUI 自带的 cell 回收;不实现桶式虚拟滚动(那是为上万 cell 设计的)。

**理由**:
- `List` 在 macOS 上自带「行高 = 50pt 左右」的视觉与「侧边选中条」风格,跟消息卡(高度不固定、含媒体网格)不适配;手动 hack row style 比直接 `ScrollView` 还麻烦
- 消息数据量小(千级以内),`LazyVStack` 的 cell 回收足够,不需要像媒体页那样做 `VirtualScrollView` + NSScrollView 桥
- 渲染结构与 vue 端 `<div class="flex flex-col gap-4 max-w-3xl mx-auto">` 同构,后续翻译样式改 CSS 语义 → SwiftUI modifier 很直接

**取舍**:
- cell 复用粒度由 SwiftUI 控制,不能像媒体页那样手控 RENDER_OVERSCAN;但消息量小,不需要
- `LazyVStack` 在 cell 高度差很大时(纯文本 vs 9 张媒体)会出现顶部 cell 还没渲染导致下方 cell 计算偏移的轻微抖动;靠 `ForEach(...).id(\.id)` + 在 cell 自身加 `frame(maxWidth: .infinity, alignment: .leading)` 兜底

**备选方案否决**:
- 复用 `MediaLibraryView` 的 `VirtualScrollView` + `NSScrollViewBridge`:消息 cell 高度不固定,虚拟滚动的「按 cell 算 offset」逻辑会跟媒体页的「按桶算」打架,迁移成本高
- `NSCollectionView` 包一层:能拿到最好的滚动性能,但用 SwiftUI 包 AppKit 的复杂度(代理、dataSource)对一个 read-only 视图来说不划算

### Decision 4: 过滤栏用 macOS 风格,不做 v-calendar 等价物

**选择**: 左侧 `FilterSidebar` 改为「macOS Finder 标记/智能文件夹」风格 —— `List(selection:)` 风格的多组条目(标签 / 演员 / Issue),每组带 section header,点条目就过滤;不实现 v-calendar 等价物(那是 vue 端的浏览器便利,Mac 端用 `DateScrubber` 替代)。

**理由**:
- macOS 原生 `List(selection:)` 风格 sidebar 已经被 SidebarView 用过,跟系统外观一致(深色模式、字体、间距、选中态)
- `DateScrubber` 已经在媒体页用上了,喂它一个消息域的 timeline(同结构,`[(year, month, day, count)]`)就能跳到指定日 —— 跟 vue 端 v-calendar 等价但更 macOS
- 不引入新依赖(macOS 系统组件够用)

**取舍**:
- 没法在 macOS 端实现 v-calendar 那种「日历上每天带颜色圆点 + 点击跳」的视觉 —— DateScrubber 是右栏的细长 scrubber,需要适应。视觉降级但功能等价
- 「演员」「标签」分组用 `Section { ForEach }`,不是搜索框即时过滤(vue 端有搜索);如果演员/标签超过 50 条,加一个 `searchable` 文本框放在 List 顶部

**备选方案否决**:
- 像素级还原 v-calendar:第三方 SwiftUI 日历组件都跟 macOS 视觉对不齐,自己写一个又超出本期范围
- 用 v-calendar for SwiftUI:不存在这个包,需要 web 端走 WKWebView 套,过度工程

### Decision 5: 媒体预览复用 `MediaDetailView`,不写新的预览组件

**选择**: 消息详情面板里的媒体网格(`MessageMediaGrid`)点击媒体 → 推入 `NavigationStack` 打开 `MediaDetailView`,逻辑与媒体页媒体网格点击完全一致。

**理由**:
- `MediaDetailView` 已经支持本地文件 URL(`Media.localFileURL`)、媒体间左右键翻页、关闭回调、键盘事件
- 不重复实现全屏预览逻辑;消息 / 媒体两个 tab 共享同一预览实现
- 后续如果给 `MediaDetailView` 加旋转 / 删除 / 标签编辑,消息详情自动受益

**取舍**:
- `MediaDetailView` 的标题来自 `PreviewTitle.shared`(由媒体页 `MediaLibraryView` 在打开预览时设置);消息流打开预览时也要 `PreviewTitle.shared.title = message.text` 或 `message.id` 对应的 `MessageDetail` 标题。沿用现有 `PreviewTitle` 单例即可
- 消息域的「上一条/下一条消息」导航不实现 —— 那是 MediaPreviewDestination 在媒体桶之间的导航,消息域是「同一消息内多张媒体」,本应只在该消息内翻;`MediaDetailView` 已经支持这一行为(传 mediaList + startIndex)

**备选方案否决**:
- 写第二个 `MessageMediaDetailView`:重复实现,后续旋转 / 删除维护成本双倍

### Decision 6: 写操作(MessagesViewModel.changeStarred 等)直接连 backend HTTP,不接本地 GRDB

**选择**: 本 change 的「仅看收藏」过滤在 feed 上 = `WHERE starred = 1` 由 SQL 完成,不需要任何写操作。用户点星标按钮(若实现)走 backend `PATCH /messages/{id}`。

**理由**:
- 与 mac-native-local-db-media-grid 的「read-only first phase」基调一致
- backend 是写操作的单一真源;本地 SQLite 是只读快照。Mac 端写不会同步到其他端(Android 也在用本地 + 后端同步)
- 当前 scope 内 MessagesViewModel 不暴露写接口(本 change 完全不实现点星标 / 删除 / 编辑),写由未来 change 单独加

**取舍**:
- 用户在 Mac 端点星标没有「立刻生效」的乐观更新 —— 等待 backend 响应再 refetch(典型延迟 50~200ms,LAN 上可接受)
- Mac 端的 DB 是 backend 的只读 mirror,backend 写后需要等 sync 同步到本地;本期假设 sync 通道已就绪(android-image-zoom / sync 能力已有)

**备选方案否决**:
- 在 Mac 端直接 UPDATE 本地 SQLite 模拟写:会破坏只读契约,可能与 Android 的本地写冲突,不符合项目「Mac 端 read-only」基调

### Decision 7: 演员头像用 `LocalImageLoader` 复用 + 加 `actorId` 命名空间

**选择**: 复用 `LocalImageLoader.shared`,key 由「`(kind, id)`」组成,`kind` 区分 `.mediaThumbnail` / `.actorAvatar`,`id` 是 mediaId 或 actorId。这样 NSCache 不会把媒体缩略图和演员头像搞混,也不会让 actorId 撞上 mediaId。

**理由**:
- `LocalImageLoader` 已有 webp 解码 + NSCache + 异步下载全部就绪,加 namespace 只是 key 维度的修改
- 避免「NSCache<NSNumber, NSImage>」在 actor 与 media 之间相互覆盖
- 改动面小:仅修改 `LocalImageLoader` 的 key 类型 + 加 `loadActorAvatar(actorId:)` 方法

**取舍**:
- `LocalImageLoader` 的现有调用方(`LocalThumbView` 走 `loadMediaThumbnail(mediaId:)`)保持不变,新增 `loadActorAvatar(actorId:)` 平行方法

### Decision 8: 状态保留:复用 mac-media-page-state-and-styling 的 ZStack 模式

**选择**: 沿用 `ContentView` 改 `ZStack { HomePlaceholderView(); MessagesView(); MediaLibraryView() }` 的模式,`MessagesViewModel` 由 `ContentView` 以 `@StateObject` 持有(与 `MediaLibraryViewModel` 同位置)。

**理由**:
- mac-media-page-state-and-styling 已经验证过 ZStack 是 macOS sidebar 标准行为,且能保持 view 树常驻
- `MessagesViewModel` 也用 `loadInitialIfNeeded` 守门(首次 onAppear 触发,后续不重置),保证切 tab 来回不丢滚动位置 / 选中消息
- 改动面小:只需把 `case .messages` 的渲染从 `MessagesPlaceholderView()` 改为 `MessagesView(viewModel: messagesViewModel)`,ZStack 与 `@StateObject` 模式已经在该 change 里就位

**取舍**:
- 三 tab 同步常驻会稍微多占内存(消息 ViewModel 持有的 messages 数组 + 媒体缩略图缓存);`LocalImageLoader` 的 NSCache 已经有内存压力回收,可接受
- 同时进行的状态保留:消息列表 + 选中消息 ID + 过滤条件(选中的 tag/actor/issue ID)+ 滚动位置(scrollTop)+ 当前查询文本。这些都放在 `MessagesViewModel` 上,`@Published` 一变 → 切回 tab 后 UI 自然恢复

## Risks / Trade-offs

- **[Risk] ISO 游标在消息快速新增时漏数据** → Mitigation:本期 read-only,数据来自 backend 同步的 SQLite 快照,「快速新增」不在本期用户场景;真要解决,游标用 `(created_at, id)` 复合,与后端契约对齐即可
- **[Risk] 演员头像 404 时 NSSound/`AsyncImage` 显式空图** → Mitigation:`LocalImageLoader.loadActorAvatar` 失败时返回 nil,UI 走 `Image(systemName: "person.circle")` 兜底
- **[Risk] 切 tab 恢复时 selectedMessage 指向的 message id 已不在 messages 列表(被 backend 删了)** → Mitigation:`onAppear` 时 `selectedMessage` 重新 fetch;fetch 404 时自动清空选中态,UI 退回到 feed 占满
- **[Risk] `LazyVStack` cell 高度差大时滚动抖动** → Mitigation:cell 自身加 `.frame(maxWidth: .infinity, alignment: .leading)`,scrollView 加 `.defaultScrollAnchor(.bottom)` 让首次进入滚到底部(对齐 vue 端)
- **[Risk] 演员 / 标签数量上千时 FilterSidebar 卡** → Mitigation:`List` 自带 cell 回收,section header 静态;若实测卡再加 `searchable` 文本框
- **[Risk] `DateScrubber` 在消息域数据稀疏(只有 10 个日期)时 scrubber 几乎是一根线** → Mitigation:scrubber 本来就是这种视觉,沿用;不为此特化
- **[Risk] `LocalImageLoader` 加 namespace 引入潜在 bug(影响现有媒体页)** → Mitigation:改动只动 `LocalImageLoader` 内部 key 构造 + 新增并行 `loadActorAvatar` 方法,不动现有 `loadMediaThumbnail` 逻辑;`LocalThumbView` 调用方不需改
- **[Risk] 消息文本带 `link` 格式时 `Text` 不能渲染** → Mitigation:本期用纯文本 + 简单 `Link` 检测(`if let url = URL(...)`);markdown 渲染等下一期再说
- **[Risk] backend 字段变 → Mac 端 DB record 字段对不上** → Mitigation:`MediaRecord` 已采用 `CodingKeys` 显式声明,本 change 同样风格;新增字段时 `MessageRecord` 显式 `try? decode`,失败抛 `RepositoryError.schemaMismatch`
- **[Risk] `ContentView` ZStack 加 MessagesView 后内存 / 启动时间** → Mitigation:MessagesViewModel 懒初始化(第一次切到 messages tab 才 loadInitial),placeholder 完全不占业务内存;实测后再调

## Open Questions

1. **Issue 入口**:vue 端 FilterSidebar 把 Issue 当作第一类过滤(右侧 PinnedBanner),Mac 端 FilterSidebar 是否同样实现?—— 本 change 默认实现「Issue 列表 + 选中过滤」(与 tag/actor 同构),PinnedBanner 不实现;若需 banner,后续单独开 change
2. **Compose 输入框**:vue 端底部有 `MessageComposeInline`,Mac 端 read-only 阶段不实现;若产品需要「Mac 端快速输入」,需要再开 write-path change
3. **预览标题**:`PreviewTitle.shared` 当前由媒体页设置(取自 `Media` 字段),消息流打开预览时设置成 `message.text`(或缩略)是否合适?—— 沿用 `PreviewTitle` 单例,内容是「消息 X」/「媒体」二选一,初步设计:消息文本截 30 字,空文本时显示「消息 #N」

## Migration Plan

不涉及后端 schema 变更 / 线上数据迁移 / 部署动作:
- backend 不动
- Vue / Android / Electron 不动
- Mac 端:把新文件加入 `MyNote.xcodeproj`(沿用 `PBXFileSystemSynchronizedRootGroup`,放入 `MyNote/MyNote/` 自动进 target;若 build system 是老的则需要在 Xcode GUI 手动加 —— 由用户在 `MyNote/MAC_TODO.md` 第 1.3 步的统一流程里带过)
- 回滚:删除新增的 4 个 Swift 文件 + `ContentView` 改回渲染 `MessagesPlaceholderView`;Xcode target 自动移除孤儿引用
- 不需要数据迁移:DB 已有 message / message_media / message_tag / media_tag / tag / actor 表,Mac 端 GRDB 直读
