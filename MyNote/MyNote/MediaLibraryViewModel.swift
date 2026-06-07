//
//  MediaLibraryViewModel.swift
//  MyNote
//
//  媒体库数据模型 - 以 timeline 为单一数据源派生 buckets,按桶懒加载 items。
//  架构对齐 vue/src/composables/useVirtualGrid.ts,保证 mac 与 web 端日期跳转行为一致。
//
//  关键不变量:
//    1. buckets 由 timeline 派生,在任意一桶被加载之前就已能算出全量布局。
//       这是「跳转到从未加载过的远期桶」能命中的根本前提。
//    2. 桶 items 进 bucketCache,key 用 "YYYY-MM-DD";状态机:idle / loading / partial / complete / error。
//    3. 可视范围 + PREFETCH 内的 idle/partial 桶进入 dwell 队列;dwell 150ms 后真正发起。
//    4. 拖动 DateScrubber 期间 dispatchPaused 关掉 dwell,只对最终落定桶 loadBucketNow。
//

import Foundation
import Combine
import CoreGraphics

// MARK: - 数据结构

/// 桶在虚拟滚动里的几何位置 + 元信息。
struct BucketLayout: Identifiable, Equatable {
    let key: String          // "YYYY-MM-DD"
    let year: Int
    let month: Int
    let day: Int
    let count: Int           // 来自 timeline
    let rows: Int            // ceil(count / cols)
    let headerOffset: CGFloat
    let gridOffset: CGFloat  // headerOffset + headerHeight
    let height: CGFloat      // headerHeight + gridH
    let endOffset: CGFloat   // headerOffset + height + WINDOW_GAP

    var id: String { key }

    var date: Date {
        var comp = DateComponents()
        comp.year = year; comp.month = month; comp.day = day
        return Calendar.current.date(from: comp) ?? Date()
    }

    var headerText: String {
        let f = DateFormatter()
        f.dateFormat = "yyyy年M月d日"
        return f.string(from: date)
    }
}

/// 桶加载状态机。
enum BucketStatus: Equatable {
    case idle           // 还没排上队
    case loading        // 在飞
    case partial        // 已经拉到一些,还有更多
    case complete       // 已加载完(达 count / 越界 / SQL 返回 < limit)
    case error
}

/// 桶 items 缓存。
struct BucketCacheEntry: Equatable {
    var status: BucketStatus = .idle
    var items: [Media] = []
    var nextCursor: String? = nil
    var loadedCount: Int { items.count }

    static func == (lhs: BucketCacheEntry, rhs: BucketCacheEntry) -> Bool {
        lhs.status == rhs.status && lhs.nextCursor == rhs.nextCursor
    }
}

/// 可视区域内一个具体 cell 的位置 + 内容。
struct VisibleCell: Identifiable {
    let bucketKey: String
    let idx: Int             // 在桶内的位置
    let x: CGFloat
    let y: CGFloat
    let size: CGFloat
    let item: Media?         // nil 表示该桶 items 还没加载到此 idx

    var id: String { "\(bucketKey)-\(idx)" }
}

// MARK: - 常量(对齐 vue 端)

private let GAP: CGFloat = 4
private let WINDOW_GAP: CGFloat = 16
private let PAGE_LIMIT = 100
private let PREFETCH_PX: CGFloat = 800
private let RENDER_OVERSCAN_PX: CGFloat = 400
private let DWELL_MS: UInt64 = 150
private let MAX_CONCURRENT = 6
private let HEADER_HEIGHT: CGFloat = 32
private let TARGET_CELL: CGFloat = 220
private let MIN_COLS = 4

// MARK: - ViewModel

@MainActor
class MediaLibraryViewModel: ObservableObject {
    // 加载状态(供 UI 顶部 spinner 等)
    @Published var isLoading = false
    @Published var errorMessage: String? = nil

    // 过滤
    @Published var selectedMediaType: String? = nil  // nil / "image" / "video"
    @Published var showOnlyStarred = false

    // Timeline 与桶布局
    @Published private(set) var timeline: [TimelineEntry] = []
    @Published private(set) var buckets: [BucketLayout] = []
    @Published private(set) var bucketCache: [String: BucketCacheEntry] = [:]

    // 滚动 + 容器测量
    @Published var scrollTop: CGFloat = 0
    @Published var viewportHeight: CGFloat = 0
    @Published private(set) var cellSize: CGFloat = TARGET_CELL
    @Published private(set) var cols: Int = MIN_COLS

    // 程序化跳转触发计数器:View 层每次值变化就把 scrollTop 推到 NSScrollView
    @Published private(set) var jumpTrigger: Int = 0
    /// 跳转目标的精确 scrollTop(写完 jumpTrigger 也会自增);View 桥读这两个。
    @Published private(set) var jumpTargetY: CGFloat = 0

    // 调度器
    private var dispatchPaused = false
    private var dwellTasks: [String: Task<Void, Never>] = [:]
    private var loadQueue: [String] = []
    private var inFlight = 0

    private let mediaSource: MediaSource

    init(mediaSource: MediaSource = LocalMediaSource()) {
        self.mediaSource = mediaSource
    }

    // MARK: - 派生属性

    var totalContentHeight: CGFloat {
        buckets.last?.endOffset ?? 0
    }

    /// 可视范围 + PREFETCH 内的桶。
    var visibleBuckets: [BucketLayout] {
        let top = scrollTop - PREFETCH_PX
        let bottom = scrollTop + viewportHeight + PREFETCH_PX
        return buckets.filter { $0.endOffset >= top && $0.headerOffset <= bottom }
    }

    /// 当前视口顶部所在桶的 date,用作 DateScrubber 圆点位置。
    var currentDate: Date {
        guard !buckets.isEmpty else { return Date() }
        let top = scrollTop
        for b in buckets {
            if b.endOffset > top { return b.date }
        }
        return buckets.last!.date
    }

    /// 渲染范围(更窄):仅 RENDER_OVERSCAN 内,实际 ZStack 里只摆这些 cell。
    var visibleCells: [VisibleCell] {
        guard cellSize > 0, cols > 0 else { return [] }
        let top = scrollTop - RENDER_OVERSCAN_PX
        let bottom = scrollTop + viewportHeight + RENDER_OVERSCAN_PX
        let rowStride = cellSize + GAP
        var out: [VisibleCell] = []
        for b in buckets {
            if b.endOffset < top || b.headerOffset > bottom { continue }
            let firstRow = max(0, Int(floor((top - b.gridOffset) / rowStride)))
            let lastRow = min(
                b.rows - 1,
                Int(floor((bottom - b.gridOffset) / rowStride))
            )
            if lastRow < 0 || firstRow > b.rows - 1 { continue }
            let startIdx = firstRow * cols
            let endIdx = min(b.count, (lastRow + 1) * cols)
            let entry = bucketCache[b.key]
            for idx in startIdx..<endIdx {
                let row = idx / cols
                let col = idx % cols
                out.append(VisibleCell(
                    bucketKey: b.key,
                    idx: idx,
                    x: CGFloat(col) * rowStride,
                    y: b.gridOffset + CGFloat(row) * rowStride,
                    size: cellSize,
                    item: entry?.items[safe: idx]
                ))
            }
        }
        return out
    }

    // MARK: - 加载入口

    /// 加载 timeline 并根据它重建桶布局。
    func loadTimeline() async {
        do {
            let tl = try await mediaSource.timeline(
                type: selectedMediaType,
                starredOnly: showOnlyStarred
            )
            print("📅 timeline loaded: \(tl.count) buckets, type=\(selectedMediaType ?? "nil"), starredOnly=\(showOnlyStarred)")
            timeline = tl
            rebuildBuckets()
        } catch {
            print("Timeline load error: \(error)")
            errorMessage = error.localizedDescription
        }
    }

    /// 第一次进入页面 / 切过滤后重置全部状态并加载 timeline。
    func loadInitial() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        // 清空桶缓存 + 滚动到顶
        bucketCache = [:]
        cancelAllDwell()
        loadQueue.removeAll()
        inFlight = 0
        scrollTop = 0
        jumpTargetY = 0
        jumpTrigger &+= 1

        await loadTimeline()
        dispatchFetches()
    }

    /// 下拉刷新 == loadInitial。
    func refresh() async {
        await loadInitial()
    }

    // MARK: - 桶布局派生

    /// 根据 timeline + cellSize + cols 重算每个桶的几何位置。
    /// timeline 为空时 buckets 也清空。
    private func rebuildBuckets() {
        guard !timeline.isEmpty, cellSize > 0, cols > 0 else {
            buckets = []
            return
        }
        var out: [BucketLayout] = []
        out.reserveCapacity(timeline.count)
        var cursor: CGFloat = 0
        let cs = cellSize
        let c = cols
        for t in timeline {
            let rows = max(1, Int(ceil(Double(t.count) / Double(c))))
            let gridH = CGFloat(rows) * cs + CGFloat(rows - 1) * GAP
            let height = HEADER_HEIGHT + gridH
            out.append(BucketLayout(
                key: bucketKey(year: t.year, month: t.month, day: t.day),
                year: t.year,
                month: t.month,
                day: t.day,
                count: t.count,
                rows: rows,
                headerOffset: cursor,
                gridOffset: cursor + HEADER_HEIGHT,
                height: height,
                endOffset: cursor + height + WINDOW_GAP
            ))
            cursor += height + WINDOW_GAP
        }
        buckets = out
    }

    // MARK: - 容器尺寸

    /// View 层在 GeometryReader 里调用,传入主滚动容器的可用宽度。
    /// 列数与 cellSize 都由它派生,变化时重算 buckets 几何。
    func setContainerWidth(_ width: CGFloat) {
        guard width > 0 else { return }
        let newCols = max(MIN_COLS, Int((width / TARGET_CELL).rounded()))
        let newCellSize = max(1, floor((width - CGFloat(newCols - 1) * GAP) / CGFloat(newCols)))
        if newCols == cols && abs(newCellSize - cellSize) < 0.5 { return }
        cols = newCols
        cellSize = newCellSize
        rebuildBuckets()
        // 几何变了,可视范围内的桶集合可能也变了,触发一次调度
        dispatchFetches()
    }

    /// View 层在 GeometryReader 里同步把容器高度交给 VM,用于可视范围计算。
    func setViewportHeight(_ height: CGFloat) {
        guard height > 0 else { return }
        if abs(viewportHeight - height) < 0.5 { return }
        viewportHeight = height
        dispatchFetches()
    }

    /// View 层的 NSScrollViewBridge 把实时 scrollTop 喂回来。
    func setScrollTop(_ y: CGFloat) {
        // clamp 在合法范围内,避免越界触发不必要的可视计算
        let maxY = max(0, totalContentHeight - viewportHeight)
        let clamped = max(0, min(y, maxY))
        if abs(scrollTop - clamped) < 0.5 { return }
        scrollTop = clamped
        dispatchFetches()
    }

    // MARK: - 跳转

    /// 跳转到指定日期对应的桶顶。`findBucketByDate` 兜底找最近一个早于等于的桶。
    func scrollToDate(_ date: Date) {
        guard let b = findBucketByDate(date) else { return }
        let maxY = max(0, totalContentHeight - viewportHeight)
        jumpTargetY = min(b.headerOffset, maxY)
        scrollTop = jumpTargetY
        jumpTrigger &+= 1  // 触发 View 把它推到 NSScrollView
        loadBucketNow(b.key)
    }

    /// 查找目标桶:精确匹配 → 最近一个 bucketDate <= date → nil。
    func findBucketByDate(_ date: Date) -> BucketLayout? {
        guard !buckets.isEmpty else { return nil }
        let target = date.year * 10000 + date.month * 100 + date.day
        for b in buckets {
            let bi = b.year * 10000 + b.month * 100 + b.day
            if bi <= target { return b }
        }
        return buckets.last
    }

    // MARK: - 加载调度

    /// 拖动 scrubber 时调 true,释放时调 false;暂停时清光 dwell timer。
    func setDispatchPaused(_ paused: Bool) {
        dispatchPaused = paused
        if paused {
            cancelAllDwell()
        } else {
            dispatchFetches()
        }
    }

    /// 把指定桶插队到加载队列首位,立即 pump。供跳转 / 详情等场景使用。
    func loadBucketNow(_ key: String) {
        cancelDwell(key)
        ensureEntry(key)
        let e = bucketCache[key]!
        if e.status == .loading || e.status == .complete { return }
        enqueue(key, priority: .urgent)
        pumpQueue()
    }

    /// 主调度:可视范围内 idle/partial 桶安排 dwell;不在可视范围内的 dwell 取消。
    private func dispatchFetches() {
        if dispatchPaused { return }
        let visibleKeys = Set(visibleBuckets.map { $0.key })
        for k in Array(dwellTasks.keys) where !visibleKeys.contains(k) {
            cancelDwell(k)
        }
        for b in visibleBuckets {
            let s = bucketCache[b.key]?.status ?? .idle
            if s == .idle || s == .partial {
                scheduleDwell(b.key)
            }
        }
    }

    private func scheduleDwell(_ key: String) {
        if dwellTasks[key] != nil { return }
        let task = Task { [weak self] in
            try? await Task.sleep(nanoseconds: DWELL_MS * 1_000_000)
            await MainActor.run {
                guard let self else { return }
                self.dwellTasks.removeValue(forKey: key)
                // 离开可视区就别加载了
                guard self.visibleBuckets.contains(where: { $0.key == key }) else { return }
                self.ensureEntry(key)
                let s = self.bucketCache[key]!.status
                if s == .idle || s == .partial || s == .error {
                    self.enqueue(key, priority: .normal)
                    self.pumpQueue()
                }
            }
        }
        dwellTasks[key] = task
    }

    private func cancelDwell(_ key: String) {
        dwellTasks.removeValue(forKey: key)?.cancel()
    }

    private func cancelAllDwell() {
        for t in dwellTasks.values { t.cancel() }
        dwellTasks.removeAll()
    }

    private enum Priority { case normal, urgent }

    private func enqueue(_ key: String, priority: Priority) {
        if let i = loadQueue.firstIndex(of: key) { loadQueue.remove(at: i) }
        if priority == .urgent {
            loadQueue.insert(key, at: 0)
        } else {
            loadQueue.append(key)
        }
        // 按到视口中心距离升序,中心桶最先
        let center = scrollTop + viewportHeight / 2
        loadQueue.sort { a, b in
            bucketDistance(a, center: center) < bucketDistance(b, center: center)
        }
    }

    private func bucketDistance(_ key: String, center: CGFloat) -> CGFloat {
        guard let b = buckets.first(where: { $0.key == key }) else { return .infinity }
        if center < b.headerOffset { return b.headerOffset - center }
        if center > b.endOffset { return center - b.endOffset }
        return 0
    }

    private func pumpQueue() {
        while inFlight < MAX_CONCURRENT, !loadQueue.isEmpty {
            let key = loadQueue.removeFirst()
            let s = bucketCache[key]?.status ?? .idle
            if s == .loading || s == .complete { continue }
            Task { [weak self] in
                await self?.runLoad(key: key)
            }
        }
    }

    private func runLoad(key: String) async {
        guard let b = buckets.first(where: { $0.key == key }) else { return }
        ensureEntry(key)
        bucketCache[key]?.status = .loading
        inFlight += 1
        defer {
            inFlight -= 1
            pumpQueue()
        }

        do {
            let afterCursor = bucketCache[key]?.nextCursor
            let (items, nextCursor, isComplete) = try await mediaSource.loadBucket(
                year: b.year,
                month: b.month,
                day: b.day,
                afterCursor: afterCursor,
                limit: PAGE_LIMIT,
                type: selectedMediaType,
                starredOnly: showOnlyStarred
            )
            var entry = bucketCache[key] ?? BucketCacheEntry()
            entry.items.append(contentsOf: items)
            if isComplete || entry.items.count >= b.count {
                entry.status = .complete
                entry.nextCursor = nil
            } else {
                entry.status = .partial
                entry.nextCursor = nextCursor
            }
            bucketCache[key] = entry
        } catch {
            bucketCache[key]?.status = .error
            print("loadBucket \(key) error: \(error)")
        }
    }

    private func ensureEntry(_ key: String) {
        if bucketCache[key] == nil {
            bucketCache[key] = BucketCacheEntry()
        }
    }

    // MARK: - 过滤

    func changeMediaType(_ type: String?) async {
        selectedMediaType = type
        await loadInitial()
    }

    func toggleStarredOnly() async {
        showOnlyStarred.toggle()
        await loadInitial()
    }

    // MARK: - 兼容旧 API(供详情 sheet 等暂用)

    /// 已加载到的全部 items 平铺,按 timeline 顺序。供详情 sheet 翻页用。
    /// 未加载的桶会被跳过(不会有空洞);详情翻到边缘时再触发 loadBucketNow。
    var loadedFlatItems: [Media] {
        buckets.flatMap { bucketCache[$0.key]?.items ?? [] }
    }
}

// MARK: - 小工具

private func bucketKey(year: Int, month: Int, day: Int) -> String {
    String(format: "%04d-%02d-%02d", year, month, day)
}

private extension Array {
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}

private extension Date {
    var year: Int { Calendar.current.component(.year, from: self) }
    var month: Int { Calendar.current.component(.month, from: self) }
    var day: Int { Calendar.current.component(.day, from: self) }
}
