## 1. 数据层:按桶懒加载

- [x] 1.1 `MediaRepository` 新增 `loadBucket(year:month:day:afterCursor:limit:type:starredOnly:)` 异步方法,起始 cursor 走「次日 00:00:00.000|2147483647」,SQL 与 `list()` 同模板,但遍历结果时遇到 `created_at < 当天 00:00:00.000` 立即截断、标记 `isComplete = true`;返回 `(items: [Media], nextCursor: String?, isComplete: Bool)`。tags 仍用现有 `fetchTags(db:mediaIds:)` 批量加载,避免 N+1
- [x] 1.2 `MediaSource` 协议加 `loadBucket` 方法签名;`LocalMediaSource` 透传给 repository;`APIMediaSource` 暂返回 `fatalError("not supported")`(只读 mac 第一阶段不走 API)
- [~] 1.3 在 `MediaRepositoryTests`(若不存在则在 Xcode test target 新建,或先靠 review)对 `loadBucket` 跑三个场景:单页内完整、多页续翻、跨视频子片段过滤;确保对齐 spec `按桶懒加载的复合 cursor 协议` 三个 Scenario — **暂跳过**:mac target 当前无 test bundle,新增需要改 .xcodeproj 并把 GRDB 暴露给 test target;改由 5.x 端到端走查覆盖,后续若加测试再补

## 2. ViewModel:timeline 驱动的桶布局 + 缓存

- [x] 2.1 新建 `BucketLayout` struct(`key/year/month/day/count/rows/headerOffset/gridOffset/height/endOffset/date`),`Identifiable` by key
- [x] 2.2 新建 `BucketCacheEntry` struct(`status: BucketStatus(.idle/.loading/.partial/.complete/.error), items: [Media], nextCursor: String?, loadedCount: Int`)
- [x] 2.3 `MediaLibraryViewModel` 重构:
  - 删除/降级现有的 `media: [Media]` 平铺数组(若仍需用于键盘选中,改为 computed `buckets.flatMap { bucketCache[$0.key]?.items ?? [] }`)
  - 新增 `@Published var buckets: [BucketLayout] = []`
  - 新增 `@Published var bucketCache: [String: BucketCacheEntry] = [:]`
  - 新增 `@Published var scrollTop: CGFloat = 0`、`@Published var viewportHeight: CGFloat = 0`、`@Published var cellSize: CGFloat = 0`、`@Published var cols: Int = 4`
  - 派生 `var totalContentHeight: CGFloat`(`buckets.last?.endOffset ?? 0`)
  - 派生 `var visibleBuckets: [BucketLayout]`(scrollTop + viewportHeight + PREFETCH_PX 内的桶)
  - 派生 `var visibleCells: [VisibleCell]`(逐桶按可视范围算 firstRow/lastRow,只生成可见 cell;loadedItem == nil 时返回占位 cell)
  - 派生 `var currentDate: Date`(buckets 第一个 `endOffset > scrollTop` 的桶的 date,无则取末桶)
- [x] 2.4 `loadTimeline()` 完成后立即触发 `rebuildBuckets()` 计算 BucketLayout 数组(基于 timeline + cellSize + cols + headerHeight 常量);timeline 为空则 `buckets = []`
- [x] 2.5 `rebuildBuckets()` 实现:遍历 timeline,累加 headerOffset/endOffset;`WINDOW_GAP = 16`、`GAP = 4`、`headerHeight = 32`(对齐 vue 端 DEFAULT_HEADER_H 量级,可微调)
- [x] 2.6 cellSize/cols 计算:`TARGET_CELL = 220`、`MIN_COLS = 4`、`GAP = 4`;Container 宽度通过 GeometryReader 注入 `setContainerWidth(_:)`,函数内重算 cellSize/cols 并触发 `rebuildBuckets()`
- [x] 2.7 实现按桶加载调度:
  - `func scheduleLoad(key:)`:dwell 150ms 后入队
  - `func loadBucketNow(key:)`:取消 dwell、urgent 入队、立即 pump
  - `func dispatchFetches()`:可视范围内 idle/partial 的桶都 scheduleLoad,可视范围外的取消 dwell
  - 队列按到视口中心距离升序;并发上限 6
  - `func runLoad(key:)`:调 `mediaSource.loadBucket(...)`,把结果 append 到 `bucketCache[key].items`,更新 status/nextCursor;失败标 `.error`
- [x] 2.8 `scrollToDate(_ date: Date)`:`findBucketByDate` → 写 `scrollTop = bucket.headerOffset`(直接修改 @Published,View 层负责把它推到 NSScrollView) → `loadBucketNow(bucket.key)`
- [x] 2.9 `findBucketByDate(_ date: Date) -> BucketLayout?`:按 timeline 顺序找第一个 `bucketDate <= date`;timeline 空时返回 nil
- [x] 2.10 `setDispatchPaused(_ paused: Bool)`:暂停时清掉所有 dwell timer;恢复时调一次 `dispatchFetches()`
- [x] 2.11 过滤切换(`selectedMediaType` / `showOnlyStarred`)清空 `bucketCache`、重新 `loadTimeline()` → `rebuildBuckets()`,并把 `scrollTop = 0`

## 3. View:虚拟化 ScrollView + NSScrollView 桥

- [x] 3.1 新建 `NSScrollViewBridge: NSViewRepresentable`,内部持有一个空的 `NSView` 作为占位;通过 `Coordinator` 监听 SwiftUI 父级的 `scrollTop` 变化,调 `enclosingScrollView?.contentView.scroll(to:)` 程序化跳转;同时监听 `NSScrollView.boundsDidChangeNotification` 回写 `scrollTop` 到 binding
- [x] 3.2 在 `MediaLibraryView.grid` 用新结构重写:
  - 外层 `GeometryReader` 注入 container 宽度高度到 ViewModel
  - `ScrollView(.vertical, showsIndicators: false)` 包裹一个 `ZStack(alignment: .topLeading) { Color.clear.frame(height: viewModel.totalContentHeight); 桶头; 可见 cell }`
  - bridge 作为 `.background(NSScrollViewBridge(scrollTop: $viewModel.scrollTop, jumpTrigger: $viewModel.jumpTrigger))`
  - 桶头用 `viewModel.visibleBuckets` ForEach,`.offset(y: bucket.headerOffset)`
  - cells 用 `viewModel.visibleCells` ForEach,`.offset(x: cell.x, y: cell.y)` + `.frame(width: cell.size, height: cell.size)`;loadedItem == nil 时渲染占位 Rectangle(Color.gray.opacity(0.15))
- [x] 3.3 删除旧的 `LazyVGrid + ScrollViewReader + _scrollToBucketIndex` 路径(MediaLibraryView 和 ViewModel 两端)
- [x] 3.4 主网格滚动时(boundsDidChange 触发 `scrollTop` 更新),View 层无需额外处理;ViewModel.currentDate 是 computed 派生,DateScrubber 自动响应

## 4. DateScrubber:修复拖动 / tooltip / 年份折叠

- [x] 4.1 `DateScrubber.dragGesture.onChanged` 改为每帧都更新 `tooltipDate` / `tooltipY` / `currentDate`;`onJump` 通过节流(`pendingJumpDate` + 单飞 `Task @MainActor`)每帧最多触发一次
- [x] 4.2 `dragGesture.onEnded` 触发 `onJumpFinal(date)`,清掉 dragging 状态,**不要再依赖 `onChanged` 首帧触发**
- [x] 4.3 修复 `timelineMinDate` / `timelineMaxDate`:在 `MediaLibraryView` 计算时,maxDate 用 `Calendar.current.date(bySettingHour: 23, minute: 59, second: 59, of: timeline.first.date)`,minDate 直接用 timeline.last.date(已经是 0 点)
- [x] 4.4 tooltip 浮层:把 tooltipBubble 移出右轨道 ZStack,作为 `.overlay(alignment: .topLeading)` 浮在 DateScrubber 主体之外;通过 `.offset(x: -bubbleW - 8, y: tooltipY - bubbleH/2)` 放在左侧;`tooltipY` clamp 在 `[20, height - 20]`
- [x] 4.5 实现年份标签防重叠:`yearLabels` 计算后按 `top` 升序排序,遍历时丢掉与上一个 kept 的 `top` 差 < 8% 的项;刻度全保留
- [x] 4.6 `MediaLibraryView` 集成:`onJump` 闭包调 `viewModel.setDispatchPaused(true); viewModel.scrollToDate(date)`;`onJumpFinal` 闭包调 `viewModel.scrollToDate(date); viewModel.setDispatchPaused(false); viewModel.loadBucketNow(targetBucket.key)`
- [x] 4.7 `DateScrubber.currentDate` 由 `@Binding` 改为 `let currentDate: Date`(单向数据流);拖动期间圆点用本地 `@State private var draggingDate: Date?` 覆盖显示,释放后清空让外部 currentDate 接管

## 5. 验证 / 端到端走查

- [~] 5.1 在 Xcode 跑 mac app,数据库至少包含跨多月的真实数据(从开发机 `DATA_ROOT` 选已有 SQLite) — **待用户在 Mac 上跑**
- [~] 5.2 验证 spec `Mac 网格基于 timeline 派生桶布局`:仅 timeline 加载完时,滚动条比例反映完整跨度 + 未加载桶有占位空间(不坍缩) — **待 Mac 上验证**
- [~] 5.3 验证 spec `任意日期跳转命中`:拖到几年前的日期释放,主网格立即跳到位 + 桶头出现 + items 异步填入 — **待 Mac 上验证**
- [~] 5.4 验证 spec `DateScrubber 拖动期间圆点 + tooltip 跟手`:拖动过程圆点和 tooltip 每帧跟随;松手触发 jumpFinal 一次 — **待 Mac 上验证**
- [~] 5.5 验证 spec `主网格滚动反向更新 scrubber 指示器`:鼠标滚轮滚动后圆点在 200ms 内平滑跟到新位置 — **待 Mac 上验证**
- [~] 5.6 验证 spec `DateScrubber 时间范围与视觉修正`:最新一天对应圆点不在 0% 顶端;tooltip 完整可见(不被裁);年份多时密集年份只保留较新一年文字 — **待 Mac 上验证**
- [~] 5.7 验证 spec `拖动 scrubber 时加载调度暂停`:慢拖经过 N 个桶时不触发 N 次 loadBucket(可加临时 print 计数);释放后命中桶被加载 — **待 Mac 上验证**
- [~] 5.8 验证回归:键盘方向键选中 + 单击/双击交互 + 类型/星标过滤切换 + 详情 sheet 翻页,均无新 regression — **待 Mac 上验证**
- [x] 5.9 写开发日志 `docs/devlog/2026-06-07.md`(或追加当天日志):记录改动、动机、验证结果
