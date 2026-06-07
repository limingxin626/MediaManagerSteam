## Context

Mac SwiftUI app 第一阶段做了 4 列网格 + Finder 风格选中 + 日级 DateScrubber，本意是给本地 SQLite 数据集提供一个 Photos 风格的快速时间定位体验。当前实现的失败面已经在 `proposal.md` 列清了，本设计文档解决三件事：

1. **数据流重组**：从「先加载 N 条 media → 客户端按天分组成 buckets」改为「先加载 timeline → 按天 buckets → 按需懒加载每个 bucket 的 items」。这是 vue 端 `useVirtualGrid` 已经在生产里跑通的模式。
2. **滚动跳转可靠化**：放弃 `LazyVGrid + ScrollViewReader` 对未渲染节点跳转这条不稳定的路径，改用单一 `ScrollView` + 内部绝对定位 + AppKit `NSScrollView` 桥接精确控制 `documentVisibleRect`。
3. **DateScrubber 交互修复**：拖动期间持续更新 `currentDate` + tooltip、修正 min/max date 边界、tooltip 不被框宽裁切、年份标签防重叠。

后端 `/media/timeline` 已支持日级聚合（`media-day-buckets` spec 已落地），`/media` 端点已支持复合 cursor `created_at|id` 倒序，本设计**不需要后端任何改动**。

## Goals / Non-Goals

**Goals:**

- 用户在 DateScrubber 上拖到任意日期，主网格 SHALL 在 200ms 内跳到对应 bucket 顶部并触发该 bucket 加载（即使该 bucket 之前从未加载过）。
- 用户拖动 scrubber 时，圆点指示器 + 日期 tooltip SHALL 每帧跟随手指。
- 主网格滚动（鼠标滚轮 / 触控板）时，scrubber 圆点 SHALL 同步跟随当前可视区域顶部 bucket 的日期。
- 网格容器 SHALL 在不加载完整 `media[]` 数组的前提下，根据 timeline 计算出**全量总高度**和**全量桶头位置**，让滚动条比例正确反映「整个媒体库的时间跨度」。
- 实现 SHALL 对 vue 端 `useVirtualGrid` / `DateScrubber.vue` 的契约做**结构性同构**，便于后续 spec 演进时两端同步。

**Non-Goals:**

- 不支持横向时间轴 / 月折叠面板等额外交互（vue 端也没做）。
- 不引入 Combine 之外的新响应式框架。
- 不动后端 timeline 接口 schema。
- 不实现写操作（删除/星标）—— mac 第一阶段仍只读，但需要保证未来加上时数据流仍然成立。
- 不做平台触屏（mac trackpad 三指惯性走 NSScrollView 默认）；focus 在 mouse / trackpad 两指滚动 + 鼠标拖 scrubber 这两条主路径。

## Decisions

### 1. 数据源:把 timeline 作为 buckets 的源头(而非 media[])

`MediaLibraryViewModel` 暴露的核心状态是 `buckets: [BucketLayout]`,由 `timeline: [TimelineEntry]` 派生而来——而不是当前的「media[] groupBy day」。timeline 在 `loadTimeline()` 一次取回**全部**日期的 count(对本地 SQLite 来说一次聚合查询,数据量可控),桶高度由 count 和列数推算。

```swift
struct BucketLayout: Identifiable {
    let key: String         // "2026-05-29"
    let year: Int; let month: Int; let day: Int
    let count: Int          // 来自 timeline
    let rows: Int           // ceil(count / cols)
    let headerOffset: CGFloat   // 桶头 y 坐标(从内容顶 0 开始)
    let gridOffset: CGFloat     // 桶网格 y 坐标 = headerOffset + headerH
    let height: CGFloat         // headerH + gridH
    let endOffset: CGFloat      // headerOffset + height + WINDOW_GAP
    var id: String { key }
}
```

每个桶的 items 按需加载到 `bucketCache: [String: BucketCacheEntry]`(同 vue `BucketCacheEntry`,状态机 `idle/loading/partial/complete/error`)。

**为什么不用 media[]+groupBy**：
- 跳转到一个未加载的天必然失败(`buckets.firstIndex` 拿不到)。
- 滚动条比例不对：UI 高度只反映已加载的几天,但实际媒体库可能跨数年。
- 内存:全量 buckets 是几百到几千个 BucketLayout(小 struct,可接受);全量 media 是几千到几万个 Media + thumbs,显然不能全加载。

**Alternative**: 维持 media[]+lazy fetch on scroll → 跳转失败,放弃。

### 2. 桶懒加载:复合 cursor 按桶范围请求(对齐 vue bucketStartCursor)

按桶加载具体 items 时,起点 cursor 用「**次日 00:00:00 | Int.max**」,终点用「**当天 00:00:00**」边界判停:

```swift
// MediaRepository 新增:
func loadBucket(
    year: Int, month: Int, day: Int,
    afterCursor: String?,    // partial 续翻时传入
    limit: Int,
    type: String?, starredOnly: Bool
) async throws -> (items: [Media], nextCursor: String?, isComplete: Bool)
```

实现逻辑(与 vue `useVirtualGrid.runLoad` 完全同构):

1. 起始 cursor: `afterCursor ?? "{次日 00:00:00.000}|2147483647"`
2. 执行 `SELECT * FROM media WHERE (created_at < ? OR (created_at = ? AND id < ?)) AND ... ORDER BY created_at DESC, id DESC LIMIT ?`
3. 遍历结果:遇到第一条 `created_at < 当天 00:00:00.000` 立即停止,标记 `isComplete = true`(已越界到上一天)
4. 否则若返回 < limit 也标记 `isComplete = true`(timeline 之外/最后一桶)
5. 否则保留 `nextCursor` 待续翻

**为什么不直接传一个 `between (dayStart, dayEnd)` 的 SQL**:vue 端走的是同一个 `/media` 分页端点,mac 也走同一个 SQL 模式,语义对齐、未来从 LocalMediaSource 切到 APIMediaSource 行为一致。

**Alternative**:每桶一次 `SELECT ... WHERE created_at >= ? AND created_at < ?`,语义更清晰但和 vue 端契约分叉,放弃。

### 3. 网格容器:弃用 LazyVGrid+ScrollViewReader,改 GeometryReader+ScrollView+ZStack 绝对定位

LazyVGrid 通过 ScrollViewReader 跳转「**还没被 Lazy 实例化**」的子节点,macOS 14 实测在跨大量未渲染节点时 anchor 计算偏差很大、或干脆静默无效。原因是 LazyVGrid 不预先报告未实例化子项的 frame,ScrollViewReader 拿不到 anchor 位置。

新方案(直接复刻 vue 端 `position:absolute` 模式):

```swift
ScrollView(.vertical) {
    ZStack(alignment: .topLeading) {
        Color.clear.frame(height: totalContentHeight)  // 占位撑高

        ForEach(visibleBuckets) { b in
            BucketHeader(b)
                .frame(height: headerH)
                .offset(y: b.headerOffset)
        }

        ForEach(visibleCells) { cell in
            MediaCellView(...)
                .frame(width: cell.size, height: cell.size)
                .offset(x: cell.x, y: cell.y)
        }
    }
}
.background(NSScrollViewBridge(scrollTopBinding: $scrollTop, jumpTrigger: $jumpTrigger))
```

- `totalContentHeight`、`visibleBuckets`、`visibleCells` 全部基于 `[BucketLayout]` + `scrollTop` + `viewportHeight` 计算(与 vue 完全同构)。
- 跳转通过 NSScrollViewBridge 调 `nsScrollView.contentView.scroll(to: NSPoint(x: 0, y: targetY))` —— 直接控制底层 NSScrollView,**与子视图是否实例化无关**。
- 滚动监听:bridge 注册 `NSScrollView.didLiveScrollNotification` + boundsChange,把 `documentVisibleRect.origin.y` 写回 `scrollTop`。

**Alternative A**: 继续 LazyVGrid,跳转前先 force scroll 到大概位置让目标桶实例化,再 anchor 跳精确位置(两步法)。脆弱、抖动,放弃。

**Alternative B**: 用 SwiftUI 4 的 `scrollPosition(initialAnchor:)` API。macOS 15+ 才稳定,我们部署目标 macOS 14,放弃。

### 4. DateScrubber:拖动期间持续更新 + tooltip 浮层

修复点:

```swift
// 拖动节流:每次 onChanged 都更新 tooltip + currentDate;onJump 用 rAF/Task 节流
.onChanged { value in
    dragging = true
    let pct = clamp01(value.location.y / height) * 100
    let date = percentToDate(pct)
    tooltipDate = date
    tooltipY = value.location.y
    currentDate = date            // ← 拖动期间圆点跟手指
    scheduleJump(date)            // ← 每帧最多一次
}

// 节流:用 Task + actor 单飞行
private func scheduleJump(_ date: Date) {
    pendingJumpDate = date
    if jumpInFlight { return }
    jumpInFlight = true
    Task { @MainActor in
        await Task.yield()        // 让出一帧
        let d = pendingJumpDate!
        jumpInFlight = false
        onJump?(d)
    }
}
```

边界与视觉:

- `timelineMaxDate = Calendar.current.date(bySettingHour: 23, minute: 59, second: 59, of: 最新天)`
- `timelineMinDate = 最早天 00:00:00`
- `tooltipBubble` 移出右轨道 ZStack,作为 `.overlay(alignment: .topLeading)` 浮在 DateScrubber 整体之外,通过 `.offset(x: -bubbleW - 8, y: tooltipY - bubbleH/2)` 放在左侧、不受 `barWidth+34` 框宽限制。
- 年份标签防重叠:`yearLabels` 计算后按 `top` 升序排,相邻 `top` 差 < 8 时只保留较新一年(逻辑直接抄 vue `DateScrubber.vue` 的 `yearLabels` computed)。

### 5. 滚动→指示器反向同步:currentDate 从 scrollTop 推断

ViewModel 暴露:

```swift
@Published var scrollTop: CGFloat = 0
@Published var viewportHeight: CGFloat = 0

var currentBucket: BucketLayout? {
    buckets.first { $0.endOffset > scrollTop } ?? buckets.last
}

var currentDate: Date {
    currentBucket?.date ?? Date()
}
```

`currentDate` 用 `@Published` 派生(用 `objectWillChange` 在 scrollTop 写入时手动触发,或用 Combine `$scrollTop.combineLatest($buckets).map`)。DateScrubber 把它绑成 `Binding` 仅读,**写入只在拖动期间**发生。

**关键**:`currentDate` 从绑定改为「View 读 ViewModel 派生值」+「拖动时 Scrubber 直接 setCurrentDate(临时覆盖)」两段。释放后下一次滚动事件回写正确值。

### 6. 跳转后的 bucket 优先加载

`scrollToDate(_ date: Date)` 实现:

1. `findBucketByDate(date)` 找到目标桶(找不到取最近一个 `bucketDate <= date`)。
2. 写 `scrollTop = bucket.headerOffset` → bridge 调 nsScrollView 跳过去。
3. `loadBucketNow(bucket.key)` 把该桶插队到加载队列首位(抢占 dwell 计时器)。
4. 加载完成 → bucketCache 更新 → visibleCells 重算 → ZStack 渲染该桶 cells。

中间过程主网格显示**空白桶头 + 占位灰块**(桶高度已知,布局不会跳),用户能立即看到「跳到位了,正在加载」。

### 7. 加载调度策略:dwell + 距离优先 + 并发上限

抄 vue `useVirtualGrid` 的:

- 可视范围 + PREFETCH_PX 内的桶进入候选。
- DWELL 150ms 后才真正发起,防止滚动经过中间桶时炸出几十个请求。
- 加载队列按「桶中心到视口中心」距离升序,中心桶最先加载。
- `MAX_CONCURRENT = 6`,GRDB queue.read 本地查询很快,这个上限基本不堵。
- `setDispatchPaused(true)` 在拖动 scrubber 期间暂停 dwell;释放后恢复,只 `loadBucketNow` 命中桶。

### 8. cellSize 自适应

`cellSize` 由 ScrollView 容器宽度决定:

```
TARGET_CELL = 220
cols = max(MIN_COLS, round(containerWidth / TARGET_CELL))
cellSize = floor((containerWidth - (cols - 1) * GAP) / cols)
```

Mac 端 MIN_COLS = 4(贴 vue 桌面端常量)。容器宽度通过 `GeometryReader` 取,变化时重算 buckets(headerOffset / endOffset 会变,需要重算)。

## Risks / Trade-offs

- **[NSViewRepresentable + SwiftUI 数据流耦合复杂]** → bridge 单一职责:对外只暴露 `scrollTop: Binding<CGFloat>` 和 `jumpTo: PassthroughSubject<CGFloat>`,内部不持有 ViewModel 引用,降低耦合。
- **[全量 buckets 数据量]** → 假设最坏 3650 天(10 年每天有内容),BucketLayout 是 ~80 字节,总 ~290KB,完全可接受。如果某天将来上到 10 万级桶才需要再考虑年折叠。
- **[拖动 scrubber 时主网格触发 loadBucket 风暴]** → `setDispatchPaused(true)` 在 onChanged 进来时设,onEnded 释放;只有最终落定桶被 `loadBucketNow` 加载。
- **[GRDB read 在主 actor 之外]** → MediaRepository 已经 `await queue.read`,本身在后台线程;ViewModel 在 @MainActor 接收数据后写 cache,符合现有约定。
- **[macOS 14 与 15 ScrollView 行为差异]** → 部署目标固定 macOS 14;不依赖 `scrollPosition` 等 macOS 15 API。
- **[buckets 在 cellSize 变化时全量重算]** → 用 Combine 把 (timeline, cellSize, cols) 三者 combineLatest,变化时一次性算完;数据量小,性能不是问题。
- **[键盘方向键选中跨未加载桶]** → 第一阶段仅在「已加载的相邻桶范围内」移动选中;到达未加载桶边界时先触发该桶 `loadBucketNow`,加载完后选中移过去。第二阶段可优化为「跨桶时先按 BucketLayout.count 算 globalIndex,跳过去再加载」。

## Migration Plan

无运行时迁移:Mac app 直读 SQLite,本设计只改 mac app 内部代码,后端零改动。回滚=git revert mac 端文件即可,后端 / vue / android 不受影响。
