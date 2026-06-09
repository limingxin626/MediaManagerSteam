# mac-message-feed Specification

## Purpose
TBD - created by archiving change mac-message-page. Update Purpose after archive.
## Requirements
### Requirement: 「消息」tab 渲染消息流主视图
Mac 端 sidebar 点击「消息」tab SHALL 渲染 `MessagesView`,不再渲染占位页。`MessagesView` 内 SHALL 包含左侧消息流 feed + (可选)右侧详情面板,默认 detail 关闭时 feed 占满整宽,点消息卡后 detail 滑入,feed 与 detail 共享 50/50 宽度(主窗口宽度 < 800pt 时强制 feed 占满)。

#### Scenario: 默认进入消息 tab
- **WHEN** 用户从「媒体」tab 切到「消息」tab
- **THEN** `MessagesView` 渲染 feed 列表,detail 面板不出现,feed 占满整宽
- **AND** 标题栏显示「消息」(`AppTab.messages.title`)

#### Scenario: 点击消息卡打开详情
- **WHEN** 用户点击 feed 中任一消息卡
- **THEN** 右侧 detail 面板滑入,展示该消息的 `MessageDetail`(完整 text、actor 头像与名字、tag chips、媒体网格、创建时间)
- **AND** feed 区域宽度收缩为 50%
- **AND** 同一消息卡上的星标按钮、媒体点击行为不变

#### Scenario: 关闭详情
- **WHEN** 用户点 detail 面板右上角「×」或按 ESC
- **THEN** detail 面板消失,feed 重新占满整宽
- **AND** 之前选中的消息仍保留在 `MessagesViewModel.selectedMessage` 中(切 tab 来回不会丢)

#### Scenario: 切到其他 tab 再切回保留状态
- **WHEN** 用户在「消息」tab 选中某条消息 + 滚动到 50% 位置,切到「主页」,再切回「消息」
- **THEN** 滚动位置、选中消息、过滤条件全部保留(mac-media-page-state-and-styling 的 ZStack 模式)

### Requirement: 消息卡组件
每条消息卡 SHALL 包含:
1. 顶部条:actor 头像(48pt 圆图,缺失时 `Image(systemName: "person.circle")`)+ actor 名字(可隐藏)+ 创建时间(相对时间如「2 小时前」)
2. 正文:`message.text`,有内容时显示,空时不显示文本区
3. tag chips:有 tag 时横向排列显示,空时不显示
4. 媒体网格:`message.mediaItems` 数量按 1/2/3+/4-6/7-9 排布(1 张 1x1 大图;2 张 1x2;3+ 走 3 列网格,前 9 张平铺,剩余显示为「+N」)
5. 底部条:星标按钮、媒体数量徽章、消息 ID(辅助 debug)

#### Scenario: 纯文本消息
- **WHEN** message 有 text 但无 media
- **THEN** 卡片只显示 actor + 文本 + 创建时间 + 底部条,不显示媒体网格区

#### Scenario: 单张媒体
- **WHEN** message 有 1 张 media
- **THEN** 媒体区显示该 media 的缩略图,占满卡宽,16:9 aspect ratio

#### Scenario: 9+ 张媒体
- **WHEN** message 有 12 张 media
- **THEN** 媒体网格按 3x3 排列前 9 张,第 10 个位置显示「+3」占位
- **AND** 点击该占位 SHALL 打开 detail 面板(不直接进预览,与 vue 端行为一致)

### Requirement: 媒体点击预览复用 `MediaDetailView`
消息详情面板的媒体网格中,点击任一媒体 SHALL 推入 `NavigationStack` 打开 `MediaDetailView`,与媒体页媒体网格点击行为完全一致 —— 支持左右键翻页、关闭回调(ESC/×/空格)、本地文件 URL。`PreviewTitle.shared.title` 在打开预览时 SHALL 被设置为该消息的「`消息 #{id}`」或文本前 30 字。

#### Scenario: 打开媒体预览
- **WHEN** 用户点击详情面板中 media 列表的第 2 张
- **THEN** `MediaDetailView` 显示该 media 的本地文件;左右键在该消息的 12 张 media 之间翻页
- **AND** 窗口标题栏显示 `PreviewTitle.shared.title` 的内容

#### Scenario: 关闭预览回到详情
- **WHEN** 用户按 ESC 或点 ×
- **THEN** `MediaDetailView` pop,回到 detail 面板,detail 面板中该 media 的星标态 / 缩略图与最新数据一致

### Requirement: 左侧过滤侧栏(标签 / 演员 / Issue)
`MessagesView` SHALL 在窗口左侧(< 800pt 时折叠为 toolbar dropdown)渲染一个 `FilterSidebar`,包含三组可多选条目:
1. **标签**(`Tag`):所有 tag,按消息数降序;点击选中,feed 只显示关联了该 tag 的消息
2. **演员**(`Actor`):所有 actor,按消息数降序;第一个特殊条目「无演员」(`actorId == 0` 的占位)
3. **Issue**:所有 issue(本 change 默认只展示进行中 issue,与 vue 端 `?status=doing` 对齐);第一个特殊条目「无 issue」

#### Scenario: 选中标签过滤
- **WHEN** 用户点击 FilterSidebar 中 tag 「#旅行」
- **THEN** feed 重新加载,只显示关联了 #旅行 标签的消息
- **AND** 切换时 feed 顶部出现「当前过滤: #旅行」徽章,带 × 按钮可清除

#### Scenario: 同时选多个过滤器互斥
- **WHEN** 用户已选中 tag,再点 actor
- **THEN** tag 选中被清除,只保留 actor 选中(vue 端同构 —— tag / actor / issue 三者只能选一个)

#### Scenario: actorId == 0 等价「无演员」
- **WHEN** 用户点击 actor 列表中的「无演员」条目
- **THEN** feed 只显示 `actor_id IS NULL` 的消息

### Requirement: 顶栏搜索与仅看收藏
`MessagesView` 顶栏 SHALL 包含:
- 搜索框(text 输入,300ms debounce 后触发 `queryText` 过滤)
- 「仅看收藏」开关(toggle 按钮,SF Symbol `star.fill`/`star`,激活态橙色)
- 刷新按钮(显式 refetch 当前页)

#### Scenario: 搜索 debounce
- **WHEN** 用户在搜索框连续输入「he」「hel」「hello」,300ms 内未继续输入
- **THEN** 只触发一次「`queryText = "hello"`」的 refetch(避免每键一次 SQL)

#### Scenario: 切换仅看收藏
- **WHEN** 用户点击「仅看收藏」toggle
- **THEN** feed 重新加载,只显示 `starred = 1` 的消息
- **AND** toggle 按钮显示为 `star.fill` 橙色

### Requirement: 顶栏日期跳转(DateScrubber 消息域)
`MessagesView` 顶栏 SHALL 渲染 `DateScrubber`,数据源为 `MessageRepository.monthlyDayCount(year, month, filters)`,行为与媒体页 DateScrubber 同构:
- scrubber 拖动到具体一天时,feed scrollTop SHALL 跳到该日的首条消息位置
- 跳转通过 `MessageRepository.list(cursor: <end-of-day>)` 重新拉取
- 数据为空时 scrubber 不渲染(沿用 mac-media-page-state-and-styling 决策)

#### Scenario: 跳转到指定日期
- **WHEN** 用户在 DateScrubber 释放在 2026-05-29
- **THEN** `MessagesViewModel.scrollToDate(2026-05-29)` 被调用
- **AND** `nextCursor` 重置,feed 用「该日 23:59:59.999999」作为 cursor 拉取
- **AND** 渲染结果按时间倒序后,scrolled 到该日第一条消息

#### Scenario: scrubber 数据为空
- **WHEN** 当前过滤条件下 timeline 为空
- **THEN** DateScrubber 不渲染,顶栏不占位(mac-media-page-state-and-styling 的 fallback 行为)

### Requirement: 消息流加载行为
`MessagesViewModel.loadInitial` SHALL:
1. 清空 messages 数组 / 选中消息 / 滚动位置
2. 拉取首屏(`limit = 20`)
3. 设置 `nextCursor` 与 `hasMore`
4. 自动滚到底部(消息流是「最新优先」,首屏默认从最新消息开始,沿用 vue 端 `scrollToBottom('auto')` 行为)

`MessagesViewModel.loadMore` SHALL:
1. 仅在 `scrollTop < 200pt` 且 `hasMore == true` 时触发(向上滚到底部附近)
2. 用 `nextCursor` 拉取下一页
3. 拼接在 messages 数组头部(消息按时间倒序,新加载的更早消息放前面)
4. 滚到时保持当前可视消息的相对位置不变

#### Scenario: 首次进入自动滚到底部
- **WHEN** 消息流首屏加载完成
- **THEN** `ScrollView` 自动滚到底部(显示最新消息)
- **AND** 不需要用户操作就能看到最新内容

#### Scenario: 向上滚动触发加载更早
- **WHEN** 用户向上滚到顶部 200pt 内
- **WHEN** `hasMore == true`
- **THEN** `loadMore` 触发,加载下一页(更早消息)拼到 messages 数组头部
- **AND** 滚动位置保持稳定(原本可视的消息不跳动)

### Requirement: 消息卡 hover 状态
macOS 上 SHALL 支持 hover 高亮:鼠标悬停在消息卡上时,卡背景变浅(`.background(Color.gray.opacity(0.08))`),底部操作栏(星标、媒体数量)显示出来。鼠标移开时恢复默认态。

#### Scenario: 鼠标悬停
- **WHEN** 鼠标悬停在消息卡上
- **THEN** 卡片背景高亮,底部操作栏显式可见
- **WHEN** 鼠标移开
- **THEN** 卡片背景与底部操作栏回到默认态

#### Scenario: 键盘 focus
- **WHEN** 消息卡被键盘选中(`selectedMessageId` 与该卡匹配)
- **THEN** 卡片显示系统级 selection 描边(`.focusEffectDisabled` 不应用,因为消息流不是虚拟网格)
- **AND** ESC 关闭 detail 面板

### Requirement: 空状态与错误展示
`MessagesView` SHALL 在以下场景显示对应视觉:
1. **首次加载中**:`ProgressView()` 居中(类似 `MediaLibraryView.isLoading && buckets.isEmpty` 分支)
2. **空数据**:`Image(systemName: AppTab.messages.systemImage)` + 「暂无消息」副标题(类似 vue 端 `messages.length === 0` 的空状态)
3. **加载失败**:`errorMessage` 浮层,带 × 关闭按钮(沿用 `MediaLibraryView.errorMessage` 模式)

#### Scenario: 加载成功但无消息
- **WHEN** 数据库中无任何 message
- **THEN** MessagesView 显示「暂无消息」空状态,无 errorMessage

#### Scenario: GRDB 读失败
- **WHEN** `MessageRepository.list` 抛 `RepositoryError`(DB 未连接 / schema 不匹配 / SQL 错误)
- **THEN** MessagesView 顶部出现红色 errorMessage 浮层
- **AND** MessagesViewModel.errorMessage 字段被设置,UI 用 toast / banner 形式展示
- **AND** 点 × 关闭 errorMessage,feed 仍可重试(用户点刷新)

### Requirement: 状态保留契约(切 tab 不丢)
`MessagesViewModel` 持有以下状态且 MUST 在切到其他 tab 再切回时全部保留:
- `messages: [Message]`
- `selectedMessage: MessageDetail?`
- `searchText: String`
- `starredOnly: Bool`
- `selectedTagId: Int?` / `selectedActorId: Int?` / `selectedIssueId: Int?`
- `scrollTop: CGFloat`(由 `ScrollView` 同步回 VM)
- `nextCursor: String?` / `hasMore: Bool`

`MessagesViewModel` 必须由 `ContentView` 以 `@StateObject` 持有,与 `MediaLibraryViewModel` 同位置、同生命周期。

#### Scenario: 切 tab 来回不丢状态
- **WHEN** 消息流加载到第 3 页,选中 message #42,过滤 tag #旅行,scrollTop 处于 800pt
- **WHEN** 用户切到「媒体」再切回「消息」
- **THEN** messages 数组、selectedMessage、过滤条件、scrollTop 全部恢复
- **AND** GRDB 不会再发一次首页查询(走 `loadInitialIfNeeded` 守门,首次 onAppear 才加载)

### Requirement: 写操作不在范围
本期 Mac 端消息流 MUST NOT 暴露任何写接口:不实现创建、编辑、删除、合并、拆分、收藏 / 取消收藏、媒体关联修改。所有写操作继续走 backend HTTP,由未来的 write-path change 单独引入。`MessagesViewModel` 不提供 `changeStarred`、`delete`、`merge`、`split`、`updateText` 等方法。

#### Scenario: 不暴露写入口
- **WHEN** 用户在消息卡上 hover 查看「星标」按钮
- **THEN** 按钮 SHALL 处于 disabled 态(`.disabled(true)`),鼠标提示「Mac 端暂不支持编辑,请到 web 端操作」(或同等文案)
- **AND** 点击不触发任何写操作 / 不发 backend 请求

#### Scenario: detail 面板的「编辑/删除」按钮
- **WHEN** 用户打开 detail 面板
- **THEN** detail 顶部条 SHALL NOT 显示「编辑」「删除」「拆分」等写操作按钮
- **AND** 只显示「× 关闭」与「星标(只读)」

