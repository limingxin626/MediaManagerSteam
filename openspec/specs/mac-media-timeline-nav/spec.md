# mac-media-timeline-nav Specification

## Purpose
TBD - created by archiving change mac-date-scrubber-fix. Update Purpose after archive.
## Requirements
### Requirement: Mac 网格基于 timeline 派生桶布局

MyNote macOS app 的 `MediaLibraryView` SHALL 在 `loadTimeline()` 完成后即可渲染出**整个媒体库**对应的桶布局（每个 bucket 有 key/headerOffset/height/endOffset），不依赖任何 `media` items 已被加载。`ScrollView` 的总内容高度 MUST 等于 `buckets.last.endOffset`，使原生滚动条比例反映完整时间跨度。

#### Scenario: 仅 timeline 加载完即可显示桶头

- **WHEN** 应用启动、`MediaLibraryViewModel.loadTimeline()` 返回 `[{2026-06-07, count:12}, {2026-05-29, count:7}, {2025-12-31, count:3}]`，但尚未加载任何 media items
- **THEN** `MediaLibraryView` 的 `ScrollView` 内容总高度 MUST 等于三个 bucket 的累计高度（每个 bucket = headerHeight + ceil(count/cols) 行 × cellSize + 行间 gap + bucket 间 WINDOW_GAP）
- **AND** 三个桶头「2026年6月7日」「2026年5月29日」「2025年12月31日」MUST 同时存在于内容流中（即使滚动到底部才能看到）

#### Scenario: 未加载的桶留出占位空间

- **WHEN** 当前只有 `2026-06-07` 这个桶的 items 被加载到 `bucketCache`
- **THEN** `2026-05-29` 桶的位置 MUST 显示其桶头 + 一片与其 count 匹配的占位区域（可为灰色背景或骨架格子）
- **AND** 占位区域的高度 MUST 等于 `bucket.height - headerHeight`，不会因为 items 缺失而坍缩

### Requirement: 按桶懒加载的复合 cursor 协议

`MediaRepository.loadBucket(year, month, day, afterCursor, limit, type, starredOnly)` SHALL 使用与 `MediaRepository.list` 同一个底层 `created_at|id` 复合 cursor 模式，但在以下两个边界条件之一发生时即把响应标记为 `isComplete = true`：

1. 遇到第一条 `created_at < {year}-{month}-{day}T00:00:00.000` 的记录（已越界到上一天）
2. 数据库返回行数 < limit（已无更多数据）

加载起点 cursor：调用方未传 `afterCursor` 时 MUST 使用 `"{next-day}T00:00:00.000|2147483647"` 作为初始游标，与 vue 端 `bucketStartCursor` 行为完全一致。

#### Scenario: 桶内首页加载

- **WHEN** 调用 `loadBucket(2026, 5, 29, afterCursor: nil, limit: 100, type: nil, starredOnly: false)`，数据库内 2026-05-29 共 7 条媒体
- **THEN** 起始 cursor MUST 解析为 2026-05-30T00:00:00.000 + Int.max
- **AND** 返回 items.count == 7，全部 `created_at` 介于 `[2026-05-29T00:00:00, 2026-05-30T00:00:00)` 之间
- **AND** `isComplete == true`（要么遇到上一天的越界记录，要么 SQL 返回 < limit）

#### Scenario: 桶内多页续翻

- **WHEN** 某天有 250 条媒体，第一次 `loadBucket(..., afterCursor: nil, limit: 100)` 返回 100 条 `isComplete = false` + `nextCursor = "{当天最后一条 created_at}|{id}"`
- **AND** 第二次 `loadBucket(..., afterCursor: nextCursor, limit: 100)` 接着翻
- **THEN** 第二次返回的 items 全部 `created_at` 仍在当天范围内
- **AND** 第三次翻到剩余 50 条 + 一条上一天的记录时 MUST 截断、`isComplete = true`

#### Scenario: 不计入视频子片段

- **WHEN** 某天数据库中有 5 条普通媒体 + 3 条 `video_media_id IS NOT NULL` 的视频帧
- **THEN** `loadBucket(...)` 返回的 items MUST 只包含 5 条普通媒体，3 条视频帧 MUST 被过滤掉（与 `timeline()` 计数口径一致）

### Requirement: DateScrubber 拖动期间圆点 + tooltip 跟手

Mac 端 `DateScrubber` 在用户按下并拖动指针的过程中 SHALL 每一次 `onChanged` 都同步更新：
- `currentDate`：圆点位置
- `tooltipDate` / `tooltipY`：日期气泡位置和文字
- 通过节流（最多每帧一次）触发 `onJump(date)` 让主网格滚动跟随

释放（`onEnded`）SHALL 触发一次 `onJumpFinal(date)`。

#### Scenario: 拖动过程圆点持续跟随

- **WHEN** 用户在 DateScrubber 上按下并垂直拖动指针，从 y=100 移到 y=400，期间产生 N 次 `onChanged` 事件
- **THEN** 每一次 `onChanged` MUST 立即更新圆点位置（`currentDate` 反映 `percentToDate(y/height*100)`）
- **AND** tooltip 气泡 MUST 跟随指针 y 坐标，文字反映对应日期
- **AND** `onJump(date)` 在拖动期间 MUST 至少被触发 1 次以上（不能只在首帧触发一次）

#### Scenario: 释放后触发 jumpFinal

- **WHEN** 用户在 y=320 处释放鼠标
- **THEN** `onJumpFinal(date)` MUST 被触发恰好 1 次，date 对应 y=320 的百分比换算结果
- **AND** `dragging` 状态 MUST 立即变 false
- **AND** tooltip 气泡 MUST 在拖动结束后消失（除非鼠标仍 hover 在 scrubber 上）

### Requirement: 任意日期跳转命中

`MediaLibraryViewModel.scrollToDate(_ date: Date)` SHALL 满足以下行为：

1. 找到目标 bucket（精确匹配该天；不存在则取 timeline 中第一个 `bucketDate <= date` 的桶；timeline 为空则 no-op）。
2. 同步把主 `ScrollView` 的 `documentVisibleRect.origin.y` 设为 `bucket.headerOffset`（或最近合法值，避免越过 maxScroll）。
3. 调用 `loadBucketNow(bucket.key)` 把该桶插队到加载队列首位。

跳转 MUST 在不依赖目标桶子视图先被实例化的前提下工作（即用户从最新桶拖到几年前的桶也能精确落到位）。

#### Scenario: 跳转到从未加载的远期桶

- **WHEN** timeline 包含 3650 天数据；用户在 DateScrubber 上拖到 2020-03-15 对应位置释放，此时 `bucketCache` 中只有最近 10 天的 items
- **THEN** 主 `ScrollView` MUST 在动画结束（≤300ms）后，可视区域顶部恰好对齐 `2020-03-15` bucket 的 `headerOffset`
- **AND** `2020-03-15` 的桶头 MUST 出现在可视区域顶部
- **AND** `loadBucketNow("2020-03-15")` MUST 被调用，该桶的 items 在网络/IO 允许的时间内填入

#### Scenario: 跳转到 timeline 不存在的日期

- **WHEN** 用户拖到 2020-02-29，但 timeline 中没有这一天（最近一个早于等于的桶是 2020-02-28）
- **THEN** `scrollToDate` MUST 退回到 `2020-02-28` 桶
- **AND** 不抛出错误，不留在原位

#### Scenario: 跳转后未加载桶展示占位

- **WHEN** 跳到 `2020-03-15` 但其 items 还在加载中
- **THEN** 可视区域 MUST 立即显示该桶的桶头（「2020年3月15日」）和占位灰格区域
- **AND** items 加载完成后 MUST 在原位填入，不发生整页跳动

### Requirement: 主网格滚动反向更新 scrubber 指示器

当用户通过鼠标滚轮、触控板、键盘 PageUp/PageDown 等方式滚动主 `ScrollView` 时（即非 scrubber 拖动来源的滚动），`DateScrubber` 圆点 SHALL 跟随当前可视区域顶部所在 bucket 的 `date`。

#### Scenario: 滚轮滚动时圆点跟随

- **WHEN** 用户用鼠标滚轮把主 `ScrollView` 滚动到 `documentVisibleRect.origin.y = 5000`，此位置落在 `2026-04-12` bucket 内
- **THEN** `DateScrubber` 圆点 MUST 在 200ms 内移动到 `dateToPercent(2026-04-12)` 对应位置
- **AND** 圆点位置 MUST 平滑过渡（动画时长 200ms ease-out）

#### Scenario: scrubber 拖动期间禁止反向回写

- **WHEN** 用户正在 scrubber 上拖动（`dragging == true`）
- **THEN** 即使主 `ScrollView` 因 `scrollToDate` 被程序化滚动，也 MUST NOT 触发反向写回 `currentDate` 覆盖用户手指位置
- **AND** 拖动释放后下一次自然滚动事件 MUST 恢复正常反向同步

### Requirement: DateScrubber 时间范围与视觉修正

`DateScrubber` 接收的 `minDate` MUST 为 timeline 最早一天的 00:00:00；`maxDate` MUST 为 timeline 最新一天的 23:59:59。tooltip 气泡 SHALL 浮在 scrubber 主体**之外**（不被 scrubber 自身 frame 宽度裁切）。年份文字标签 SHALL 在相邻 `top` 百分比差 < 8 时只保留较新一年（与 vue 端 `DateScrubber.vue` 同款防重叠）。

#### Scenario: maxDate 包含最新一天全天

- **WHEN** timeline 最新桶为 2026-06-07
- **THEN** 传入 DateScrubber 的 `maxDate` MUST 等于 `2026-06-07T23:59:59`，而非 `2026-06-07T00:00:00`
- **AND** 圆点初始位置 MUST 对应「最新一天结束」附近，而非「最新一天开始」（避免最新一天压在 0% 顶端）

#### Scenario: tooltip 浮出 scrubber 之外

- **WHEN** scrubber 总宽 ~62pt，用户在 scrubber 上 hover
- **THEN** tooltip 气泡 MUST 显示在 scrubber **左侧**（x 偏移到负方向），且完整可见、不被裁切
- **AND** 气泡的 y 位置跟随指针，限制在 `[20, height - 20]` 区间内防止超出

#### Scenario: 相邻年份标签折叠

- **WHEN** timeline 数据量小，相邻两年的标签算出来 `top` 差只有 5%
- **THEN** 只渲染较新一年的文字标签
- **AND** 两年的长刻度本身 MUST 全部保留（折叠的只是文字）

### Requirement: 拖动 scrubber 时加载调度暂停

当用户开始在 DateScrubber 上拖动（`onChanged` 首次触发），`MediaLibraryViewModel` 的桶加载调度器 SHALL 暂停 dwell 计时器，避免拖动经过几十个桶时炸出大量加载请求。拖动释放（`onEnded` 或 `onJumpFinal`）SHALL 恢复调度，并仅对最终落定桶触发 `loadBucketNow`。

#### Scenario: 拖动经过中间桶不发起加载

- **WHEN** 用户从最顶端一路拖到最底端，期间指针经过 200 个桶
- **THEN** 这 200 个中间桶 MUST NOT 触发任何 `loadBucket(...)` 调用
- **AND** 仅释放点对应的最终桶 MUST 触发 `loadBucketNow`

#### Scenario: 释放后恢复正常调度

- **WHEN** 用户释放 scrubber，主网格滚动到目标桶
- **THEN** 调度器 MUST 恢复 dwell 模式，可视范围内的桶按 150ms dwell 正常加载
- **AND** 此后任何主网格滚动 MUST 再次正常触发预加载

