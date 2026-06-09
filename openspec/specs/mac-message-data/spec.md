# mac-message-data Specification

## Purpose
TBD - created by archiving change mac-message-page. Update Purpose after archive.
## Requirements
### Requirement: Mac 端通过 GRDB 直读消息数据
Mac app SHALL 通过 `LocalDatabase` 的只读 GRDB 连接直接查询 `message` / `message_media` / `message_tag` / `media_tag` / `tag` / `actor` 六张表,返回与 backend `GET /messages/with-detail` 路由字段对齐的 UI 模型,过程中 MUST NOT 走 backend HTTP、不需要 backend 进程在运行。

#### Scenario: 首次打开消息 tab 加载首页
- **WHEN** 用户点击 sidebar 切到「消息」tab 且 `MessagesViewModel` 尚未加载过任何消息
- **THEN** `MessageRepository.list(cursor: nil, ...)` 发起一次 GRDB 只读事务
- **AND** 返回的消息数组按 `created_at DESC, id DESC` 排序
- **AND** feed 视图渲染 `min(20, items.count)` 条消息卡

#### Scenario: backend 不可用时仍可浏览消息
- **WHEN** backend FastAPI 进程未启动
- **THEN** Mac 端仍然能加载并显示消息列表(走本地 SQLite 快照)
- **AND** 不会出现「网络错误」「连接失败」类错误提示

### Requirement: 消息 UI 模型字段对齐 backend schema
`Message` UI 模型 MUST 至少包含 `id: Int`、`text: String?`、`createdAt: String` (ISO)、`updatedAt: String?`、`starred: Bool`、`actorId: Int?`、`actorName: String?`、`issueId: Int?`、`issueTitle: String?`、`mediaCount: Int`、`mediaItems: [MessageMediaItem]`、`tags: [MessageTag]`;字段命名、类型、nullability MUST 与 backend `MessageDetailResponse` Pydantic schema 一一对应。`MessageMediaItem` 至少包含 `id`、`filePath`、`fileUrl`、`thumbPath`、`thumbUrl`、`mimeType`、`width`、`height`、`durationMs`、`starred`、`createdAt`、`updatedAt`、`tags`。`MessageTag` 至少包含 `id`、`name`、`category`。

#### Scenario: 模型解码匹配 backend 响应
- **WHEN** DB 记录中某条 message 的 `text = "hello #world"`,`actor_id = 1`,`starred = 1`,`created_at = 2026-05-29T18:00:00`
- **THEN** 对应 `Message` UI 模型 SHALL 是 `id != 0`,`text == "hello #world"`,`actorId == 1`,`actorName == <actor.name>`,`starred == true`,`createdAt == "2026-05-29T18:00:00.000000"`

#### Scenario: actor 为空时的 null 处理
- **WHEN** DB 记录中 message 的 `actor_id IS NULL`
- **THEN** `Message.actorId == nil` 且 `Message.actorName == nil`,UI 走「无 actor」分支(隐藏头像与名字)

#### Scenario: 没有关联媒体时
- **WHEN** DB 记录中 message 没有 `message_media` 记录
- **THEN** `Message.mediaItems == []` 且 `Message.mediaCount == 0`,UI 走「无媒体」分支(不渲染媒体网格)

### Requirement: ISO 简单游标分页
`MessageRepository.list(cursor, limit, filters) -> (items, nextCursor, hasMore)` SHALL 使用 ISO `created_at` 字符串游标,无复合 id 兜底(消息量级在千条以内,不出现同一毫秒多条)。cursor 解析失败 MUST 抛 `RepositoryError.invalidCursor`,被 Repository 层拦截,不让坏 cursor 走到 SQL。

#### Scenario: 首屏加载
- **WHEN** `cursor == nil`
- **THEN** SQL 为 `SELECT ... FROM message ORDER BY created_at DESC, id DESC LIMIT (limit + 1)`
- **AND** 返回的 `hasMore = items.count > limit`,`nextCursor = items[limit-1].createdAt`(截断后最后一条的 ISO)
- **AND** 实际返回数组是 `items.prefix(limit)`

#### Scenario: 续翻更早消息
- **WHEN** `cursor = "2026-05-29T18:00:00.000000"`(已加载的最后一条)
- **THEN** SQL 增加 `WHERE created_at < ?` 条件,继续 ORDER BY DESC + LIMIT
- **AND** `hasMore == false` 时 `nextCursor == nil`,UI 显示「已经到底了」

#### Scenario: cursor 格式非法
- **WHEN** `cursor = "not-a-date"`
- **THEN** `MessageRepository.list` 抛 `RepositoryError.invalidCursor("not-a-date")`
- **AND** MessagesViewModel 把错误显示为 toast「无效的分页游标」并停止续翻

### Requirement: 过滤参数语义对齐 backend
`MessageRepository.list` MUST 支持以下过滤参数,且与 backend `GET /messages/with-detail` 路由的 WHERE 子句语义一致:
- `actorId: Int?` — `actor_id = ?`;`actorId == 0` 代表「无 actor」,`actor_id IS NULL`;`nil` 代表不过滤
- `tagId: Int?` — `(message.id IN (SELECT message_id FROM message_tag WHERE tag_id = ?) UNION SELECT message_id FROM message_media JOIN media_tag ... WHERE media_tag.tag_id = ?)`,沿用 backend 的「message 直连 tag」+ 「message 关联的 media 也带这个 tag」两种来源的并集
- `issueId: Int?` — `issue_id = ?`;`issueId == 0` 代表 `issue_id IS NULL`
- `queryText: String?` — `text LIKE '%' || ? || '%'`(大小写不敏感)
- `mediaId: Int?` — `message.id IN (SELECT message_id FROM message_media WHERE media_id = ?)`
- `starredOnly: Bool` — `starred = 1`

#### Scenario: 多过滤组合
- **WHEN** `actorId = 1, starredOnly = true, queryText = "hello"`
- **THEN** SQL 同时应用 `actor_id = 1 AND starred = 1 AND text LIKE '%hello%'`
- **AND** 命中数由分页 limit 控制

#### Scenario: mediaId 过滤返回关联消息
- **WHEN** `mediaId = 42`,且 message #5 / #8 都关联了该 media
- **THEN** 返回的消息数组 MUST 包含 message #5 和 message #8
- **AND** 数组中每条消息的 `mediaItems` MUST 包含 mediaId = 42 的那项

### Requirement: 批量预取 tag 与 actor,避免 N+1
`MessageRepository.list` 在加载一页消息时 SHALL 用单条 SQL 批量加载:
1. 这页所有消息关联的 `tag`(经 `message_tag` 和 `media_tag` 合并去重,沿用 backend `_aggregate_tags` 逻辑)
2. 这页所有 message 的 `actor`(`WHERE id IN (?, ?, ...)`)
3. 这页所有 `message_media` 行及其 `media` 字段

不应在 Swift 层做 N+1(每条 message 单独查 tag/actor/media)。`media` 字段复用现有 `MediaRecord` 读取(共享 `LocalThumbView` / `MediaDetailView` 路径)。

#### Scenario: 加载 20 条消息
- **WHEN** `limit = 20`,这 20 条共有 12 个不同 actor、35 个不同 tag、48 张 media
- **THEN** `MessageRepository.list` 内部 SHALL 最多发 4~6 条 SQL(1 主查询 + 1 actor 查询 + 1 tag 查询 + 1 message_media 查询 + 1 media 查询)
- **AND** SQL 总量 MUST NOT 与消息数线性相关(20 条消息也只发 4~6 条)

### Requirement: 日期时间线
`MessageRepository.monthlyDayCount(year, month, filters) -> [DayCount]` SHALL 返回该月有消息的所有日期 + 消息数,只读 `message` 表(不需要 JOIN media)。返回结构与 `MediaRepository.timeline` 形同:`[(year: Int, month: Int, day: Int, count: Int)]`,按 `year DESC, month DESC, day DESC` 排序。filters 应当与 `list` 共享同一组过滤(同 SQL builder 复用),保证 timeline 的「该日有消息」与 feed 的「该消息是否被过滤掉」一致。

#### Scenario: 该月无消息
- **WHEN** `year = 2025, month = 1`,且该月无任何 message
- **THEN** 返回空数组
- **AND** DateScrubber 收到空 timeline 时不渲染(mac-media-page-state-and-styling 的 fallback)

#### Scenario: 与 actor/tag 过滤组合
- **WHEN** `actorId = 1` 且 2026-05-29 有 3 条 message 都属于该 actor
- **THEN** timeline 中 `2026-05-29` 的 `count` MUST 等于 3(只算该 actor 的消息,不算别的 actor 在同一天的消息)

### Requirement: 演员头像本地 URL
`Actor` UI 模型 MUST 暴露 `localAvatarURL: URL?`,指向 `{DATA_ROOT}/data/actor_cover/{id}.webp`(`Settings.dataRoot == nil` 时返回 nil)。`DATA_ROOT` 不可用时 UI MUST 走兜底 `Image(systemName: "person.circle")` 而不是显示破损图片。

#### Scenario: 演员头像命中
- **WHEN** `Settings.dataRoot` 已配置,且 `{DATA_ROOT}/data/actor_cover/1.webp` 存在
- **THEN** `actor.localAvatarURL != nil`,UI 加载该 URL 的 webp 显示

#### Scenario: 演员头像缺失
- **WHEN** `{DATA_ROOT}/data/actor_cover/1.webp` 不存在(老数据未生成头像)
- **THEN** `LocalImageLoader.loadActorAvatar(actorId: 1)` 返回 nil
- **AND** UI 渲染 `Image(systemName: "person.circle")` 占位

### Requirement: 媒体本地 URL 复用既有契约
`MessageMediaItem` 的 `localThumbURL` / `localFileURL` MUST 沿用 `Media` 的既有扩展(`Models.swift` 已实现)—— 把 message 关联的 media 字段直接构造为 `Media` UI 模型,再读 `.localThumbURL` / `.localFileURL`。这样消息流媒体缩略图、媒体流媒体缩略图、消息详情媒体点击预览都走同一份 `LocalThumbView` / `LocalImageLoader` / `MediaDetailView`。

#### Scenario: 消息内缩略图与媒体网格使用同一渲染路径
- **WHEN** 消息详情面板渲染 `message.mediaItems[i]`
- **THEN** 该 cell 调用的 `LocalThumbView` / `LocalImageLoader.loadMediaThumbnail(mediaId:)` 与媒体网格的 `MediaGridItem` 走完全相同代码路径
- **AND** 不需要为消息域单独写一份缩略图渲染

