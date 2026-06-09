## Why

Mac 端 MediaLibraryView 刚加的「无限滚动 + DateScrubber 日期导航」效果不可用：

- **跳转默认无效**：DateScrubber 拖到 2025 年某天，`buckets` 只来自已加载到 `viewModel.media[]` 的少数最新天，`buckets.firstIndex(where:)` 命中不到 → `_scrollToBucketIndex` 保持 `nil`，UI 完全没反应。
- **跳转 even 命中也会失效**：`ScrollViewReader.scrollTo("header-\(id)")` 在 `LazyVGrid` 里对**未实例化**的子节点 macOS 下经常无效。
- **指示器拖动时不跟随**：`dragGesture` 只在 `onChanged` 首帧调一次 `onJump`，第二帧及以后丢掉；`currentDate` 只在 `onEnded` 写一次 — 拖动过程中圆点不动。
- **轴刻度位置不准**：`timelineMaxDate` 取的是最新一天的 0 点，不是 23:59:59，导致最新一天压在 0% 顶端，年份标签全堆在轴顶。
- **气泡被裁切**：DateScrubber 整框 `.frame(width: barWidth + 34)`=62，但 tooltip `.position(x: barWidth + 20)` 超出框边界，显示位置错或被裁。
- **架构不对等**：vue 端 `useVirtualGrid` 已有「timeline 驱动桶布局 + 复合 cursor 按桶范围加载 + 拖动节流跳转」的成熟方案；mac 端只是把 `media[]` 按 client-side 分组，没法支持任意日期跳转。

## What Changes

- **架构对齐**：把 vue `useVirtualGrid` 的核心模式移植到 mac —— `buckets` 直接由 `timeline` 推导（不需要先加载 media），bucket 按需懒加载。
- **新增按桶加载**：`MediaRepository` / `MediaSource` 新增 `loadBucket(year, month, day, ...)` 方法，使用「次日 00:00:00 | Int.max」复合 cursor 起点 + 「日 00:00:00」边界判停，对齐 vue 端 `bucketStartCursor` 契约。
- **重写 ViewModel**：`MediaLibraryViewModel` 改为以 `[BucketLayout]`（timeline → key+count+预估行数）作为单一数据源，按可视范围 dispatch 加载具体桶的 items 到 `bucketCache: [String: BucketItems]`。
- **重写网格容器**：放弃 `LazyVGrid + ScrollViewReader` 跨桶跳转的不可靠路径，改用单一垂直 `ScrollView` + 内部 `ZStack` 绝对定位渲染可视范围内的 cells（与 vue `visibleCells` 同构），跳转通过设置 `scrollTop` + AppKit `NSScrollView` 桥接实现精确定位。
- **DateScrubber 修复**：
  - `dragGesture.onChanged` 每帧都更新 `tooltipDate`、`tooltipY`，并每帧节流触发 `onJump`；`currentDate` 在拖动期间也跟随更新。
  - `timelineMaxDate` 取「最新一天 23:59:59」；`timelineMinDate` 取「最早一天 00:00:00」。
  - tooltip 改用相对 `barRef` 的 overlay，浮在 DateScrubber 之外（不再受 `barWidth+34` 框宽限制）。
  - 年份标签防重叠：相邻 `top` 差 <8% 时只保留较新一年（对齐 vue 行为）。
- **滚动同步**：滚动主网格时，根据 `scrollTop` 推断当前 bucket，反向更新 `currentDate` 让 scrubber 圆点跟随（vue `currentDate` computed 的 swift 对等)。

## Capabilities

### New Capabilities
- `mac-media-timeline-nav`: Mac 端 MediaLibraryView 的虚拟化网格 + 右侧日期导航条，覆盖按桶懒加载、任意日期跳转、滚动位置同步、拖动预览交互的端到端行为契约。

### Modified Capabilities
（无 — `media-day-buckets` / `media-timeline` 现有 spec 描述的是 vue 端 + 后端契约，本次只在 mac 端新增对等能力，不修改已有 spec 的 requirements。）

## Impact

- **Swift 代码**：
  - `MyNote/MyNote/MediaRepository.swift` — 新增 `loadBucket(...)` 方法；timeline 已有日级聚合无需改后端。
  - `MyNote/MyNote/MediaSource.swift` — 协议加 `loadBucket`，`LocalMediaSource` / `APIMediaSource` 分别实现。
  - `MyNote/MyNote/MediaLibraryViewModel.swift` — 大改：以 timeline 为数据源建 `buckets`，引入 `bucketCache`、`visibleRange`、`scrollTop` 状态；移除 `media: [Media]` 平铺数组（或改成只服务键盘选中、preview 拼接用）。
  - `MyNote/MyNote/MediaLibraryView.swift` — 重写 grid 容器：弃用 `LazyVGrid + ScrollViewReader`，改用 `GeometryReader + ScrollView + ZStack` 绝对定位；通过 NSViewRepresentable 桥到 `NSScrollView` 完成精确 `scrollTo` 跳转。
  - `MyNote/MyNote/DateScrubber.swift` — 修复拖动跟随、tooltip 位置、年份标签防重叠、min/max date 边界。
- **不动**：后端 `/media/timeline`、`/media` 端点契约不变；Android、Vue、Electron 代码无影响；现有 spec `media-day-buckets` / `media-timeline` 不修改。
- **Xcode 端**：无新增 SPM 依赖，无 Info.plist 改动。
