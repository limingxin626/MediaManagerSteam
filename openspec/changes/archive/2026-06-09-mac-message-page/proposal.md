## Why

Mac 端「消息」tab 当前只有占位页 `MessagesPlaceholderView`,点进去只看到「敬请期待」三字,完全不可用。Vue 端 `vue/src/views/Message.vue` 已经实现了一套完整的消息流(消息卡片列表 + 媒体缩略图网格 + 详情面板 + 标签/演员/Issue 侧栏过滤 + 日期跳转 + 合并/拆分/编辑),是用户在 Web/Electron 上的主要浏览入口。Mac 端 SwiftUI 是当前主推端(`MyNote/MAC_TODO.md` 把它列为主路径,GRDB 直读 SQLite、不依赖 backend),缺这个 tab 让 Mac 端实际只能浏览媒体,没有进入「按时间流回顾」的能力。功能差距与产品定位不匹配,本次把它补齐。

## What Changes

- **替换占位页** —— `MessagesPlaceholderView` 删掉,改用 `MessagesView` + `MessagesViewModel` 重新填充 `.messages` tab;`ContentView` 里 `case .messages` 改为渲染 `MessagesView`,与媒体页同一路径(`@StateObject` 提到 `ContentView` 持有)
- **数据层** —— 新增 `MessageRepository`(`MyNote/MyNote/MessageRepository.swift`),通过 `LocalDatabase` GRDB 只读连接查 `message` / `message_media` / `tag` / `actor` / `media_tag` / `message_tag` 六张表;对齐 vue 端 `useApi.get('/messages/with-detail', ...)`,支持 cursor 分页(ISO `created_at` 游标,与 web 端 `Messages` 路由相同的「`created_at` 简单游标」规格)+ `actor_id` / `tag_id` / `issue_id` / `query_text` / `media_id` / `starred` 过滤
- **记录映射** —— 新增 `MessageRecord` / `MessageMediaRecord` / `ActorRecord` / `TagRecord`(`MyNote/MyNote/MessageRecord.swift`),字段与 backend `app/models/__init__.py` 一一对应(沿用现有 `MediaRecord` 的 snake_case `CodingKeys` 风格)。把 `Models.swift` 里的 `Message` / `MessageMediaItem` / `MessageTag` 改为「DB record + UI struct」两层,UI struct 持有可空 ISO 字符串、computed `localThumbURL` / `localFileURL`(复用 `Media` 已有的扩展模式)
- **演员缩略图** —— 新增 `ActorRecord.localAvatarURL`(`{DATA_ROOT}/data/actor_cover/{id}.webp`)。`LocalImageLoader` 已支持 webp 解码,直接复用 `LocalImageLoader.shared` 的 `NSCache<NSNumber, NSImage>` 加一个 actor namespace(用 `id` 空间隔离 actor 头像 vs 媒体缩略图)
- **视图层** —— `MessagesView`(`MyNote/MyNote/MessagesView.swift`)采用与 vue 端 Message.vue 同构的左 feed + 右 detail 双栏布局。Feed 走 `LazyVStack` + 简单分页(消息数量远小于媒体,不需要桶模型);Detail 面板点击消息卡后从右侧滑入(NavigationSplitView 同一 detail 容器内嵌 `HSplitView`,或简化为 detail 区域整体根据 `selectedMessage != nil` 切布局),承载 `MessageDetail` 全字段 + 媒体网格
- **侧栏过滤** —— `FilterSidebar`(标签/演员/Issue)在 mac 端沿用 macOS 风格:`List(selection:)` 风格的左侧 filter pane,展示标签 / 演员 / Issue 列表(与 macOS Finder 「标记」「人物」等过滤逻辑对齐);Issue 入口本期不强制,但结构上预留(只读浏览)
- **日期跳转** —— 复用 `MediaRepository.timeline` 的思路新增 `MessageRepository.monthlyDayCount`(轻量,只返回有消息的日期集合),驱动一个简化版 `DateScrubber`(沿用现有 `DateScrubber` 组件,但喂入 message 域的 timeline)
- **macOS 风格取舍** —— 不直接搬 vue 端的像素级 UI(留出后续与 mac-media-page-state-and-styling 类似的 macOS 风格打磨余地),先确保功能对齐:feed 列表、消息卡、媒体网格、详情面板、过滤、日期跳转、媒体预览(直接复用 `MediaDetailView` 即可)
- **不在范围** —— 创建/编辑/删除消息、合并、拆分、上传新消息、Issue 创建 —— 这些写操作继续走 backend HTTP,本期 Mac 端仍只读(与 `mac-native-local-db-media-grid` capability 的「read-only first phase」一致)
- **不在范围** —— 消息搜索文本高亮、tag 全文索引、@mention 解析、@actor 自动补全 —— 沿用 vue 端用 `query_text` 模糊搜索即可

## Capabilities

### New Capabilities
- `mac-message-feed`: Mac 端消息流主能力 —— 通过 GRDB 直读 SQLite 渲染消息卡片列表(feed)+ 媒体网格 + 详情面板,支持标签/演员/Issue/搜索/星标过滤,日期跳转,媒体预览(复用 `MediaDetailView`)
- `mac-message-data`: Mac 端消息数据层 —— `MessageRepository` / `MessageRecord` / `MessageMediaRecord` / `ActorRecord` / `TagRecord` 与 backend SQLAlchemy schema 的对齐契约,以及 cursor 分页 / 过滤 / 批量预取的 SQL 行为

### Modified Capabilities
<!-- 无现有 mac-* capability 直接覆盖消息流。`mac-native-local-db-media-grid` 是媒体域,不重用。`mac-media-grid-selection` 仅讲媒体网格选中态,不涉及消息。 -->
无修改。

## Impact

- 新增文件
  - `MyNote/MyNote/MessagesView.swift` —— 消息流主视图
  - `MyNote/MyNote/MessagesViewModel.swift` —— 数据 / 状态 / 分页 / 过滤
  - `MyNote/MyNote/MessageRepository.swift` —— GRDB 数据访问层
  - `MyNote/MyNote/MessageRecord.swift` —— DB record 映射(单文件内放 Message / MessageMedia / Actor / Tag 四张表的 record)
- 修改文件
  - `MyNote/MyNote/ContentView.swift` —— `case .messages` 改为渲染 `MessagesView`,`MessagesViewModel` 由 `ContentView` 持有(与 `MediaLibraryViewModel` 同位置,保证切 tab 不丢状态)
  - `MyNote/MyNote/MessagesPlaceholderView.swift` —— 删掉(或保留为 deprecated 占位,等 Xcode 端确认)
  - `MyNote/MyNote/Models.swift` —— 把 `Message` / `MessageMediaItem` 改为「DB record + UI struct」两层;UI struct 持有可空 ISO 字符串 + computed `localThumbURL` / `localFileURL`;`MessageTag` 不动(已是纯 UI struct)
  - `MyNote/MyNote/LocalImageLoader.swift` —— 加 actor 头像 namespace(用 `Actor` 类型作为 key 前缀,避免与媒体缩略图缓存冲突)
- 不影响
  - backend / Vue / Android / Electron 端
  - `MediaLibraryView` / `MediaRepository` / `MediaRecord` 媒体相关代码
  - `AppTab` 枚举、`SidebarView` 导航结构
  - `Settings` / `OnboardingView` / `DataRootPicker` 数据目录相关
- 关联但不改
  - `MediaDetailView` —— 直接复用,作为消息详情面板里媒体网格点击后的预览 destination
  - `DateScrubber` —— 直接复用,把 message 域的 timeline 喂给它
  - `LocalImageLoader` 已有 webp 解码 + `NSCache`,只在 key 维度加命名空间
- 数据语义
  - 「读」:SQL 口径与 backend `messages/with-detail` 路由对齐(`message.id DESC` 排序,游标即 `created_at` ISO 字符串)
  - 「不读」:backend 写的「`#hashtag` 自动解析」「`message_service` 合并/拆分」逻辑 —— 本期 Mac 端不接写操作
