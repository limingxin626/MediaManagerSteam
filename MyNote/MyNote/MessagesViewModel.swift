//
//  MessagesViewModel.swift
//  MyNote
//
//  消息流数据 / 状态 / 分页 / 过滤 —— 与 vue 端 Message.vue 的 reactive state 同构,
//  走 GRDB 直读 SQLite(不依赖 backend)。架构对齐 MediaLibraryViewModel:
//
//    1. 单一数据源:messages: [Message] 是 feed 的全量数据(已加载的),分页
//       loadMore / selectFilter 都基于这个数组 + nextCursor。
//    2. 状态保留:ContentView 以 @StateObject 持有本 VM,切 tab 来回不丢。
//    3. 写操作为空:Mac 端 read-only 阶段,所有 mutation 走 backend HTTP,本
//       VM 不暴露 changeStarred / delete / merge / split 等方法。
//    4. selectedMessage:full detail(actor / mediaItems / tags)由 fetchMessageDetail
//       单独拉,不走 list(避免 detail 拿不到完整 9+ 媒体)。
//

import Foundation
import Combine

@MainActor
final class MessagesViewModel: ObservableObject {

    // MARK: - Published 状态

    /// feed 当前已加载的消息列表(按 created_at DESC, id DESC)。
    @Published private(set) var messages: [Message] = []
    /// 用户当前选中的消息完整 detail(null = 未选中,detail pane 关闭)。
    @Published var selectedMessage: Message? = nil
    /// 单条 detail 拉取中的 loading 标志(消息卡 hover → 选中期间过渡)。
    @Published private(set) var selectedMessageLoading = false

    @Published private(set) var isLoading = false
    @Published var errorMessage: String? = nil

    // 搜索 / 星标过滤
    @Published var searchText: String = ""
    @Published var starredOnly: Bool = false

    // 侧栏过滤(tag / actor / issue 三选一互斥)
    @Published var selectedTagId: Int? = nil
    @Published var selectedActorId: Int? = nil
    @Published var selectedIssueId: Int? = nil

    // 分页
    @Published private(set) var nextCursor: String? = nil
    @Published private(set) var hasMore: Bool = true

    // 滚动
    @Published var scrollTop: CGFloat = 0

    // 月度 timeline(DateScrubber 渲染所需)
    @Published private(set) var monthlyDayCount: [DayCount] = []

    // 过滤侧栏条目
    @Published private(set) var availableTags: [Tag] = []
    @Published private(set) var availableActors: [Actor] = []
    @Published private(set) var availableIssues: [Issue] = []

    /// prepend 完成后,View 应该 scrollTo 的 message id(由 loadMore 的 restoreAnchor
    /// 参数写入;View 在 messages.count 变化时 consume 一次)。
    @Published private(set) var prependedPendingAnchor: Int? = nil

    /// scrollToDate 之后 ~500ms 内为 true。View 在 prefetch marker 触发时
    /// 检查它,避免跨日期边界拉到不该出现的旧消息。
    @Published private(set) var dateJumpPending: Bool = false

    // MARK: - 依赖

    private let repository: MessageRepository

    /// 首次 onAppear 守门 —— 切 tab 来回不重置状态(同 MediaLibraryViewModel)。
    private var hasLoadedOnce = false
    private var debounceTask: Task<Void, Never>? = nil

    // MARK: - VM 加固(prefetch 稳健性)

    /// 每次 loadInitial / selectFilter / scrollToDate 入口 +1。loadMore 入口
    /// 捕获 `myGen`,await 结束后若 `myGen != requestGeneration` 说明期间切了
    /// 过滤/日期 → 丢弃结果(否则旧 filter 的旧 cursor 拿到数据会污染新 filter 的 feed)。
    private var requestGeneration: Int = 0
    /// 清 task handle —— scrollToDate 期间切换可以取消前一个 500ms 等待。
    private var dateJumpClearTask: Task<Void, Never>? = nil
    /// loadMore debounce:200ms 内重复触发直接拒绝(兜底 LazyVStack cell 复用时
    /// 同一 marker view 被多次 onAppear 调到的极端情况)。
    private var lastLoadMoreAt: Date? = nil

    // MARK: - 初始化

    init(repository: MessageRepository = MessageRepository()) {
        self.repository = repository
    }

    // MARK: - 过滤拼装

    private var currentFilter: MessageFilter {
        MessageFilter(
            actorId: selectedActorId,
            tagId: selectedTagId,
            issueId: selectedIssueId,
            queryText: searchText.isEmpty ? nil : searchText,
            mediaId: nil,
            starredOnly: starredOnly
        )
    }

    // MARK: - 加载入口

    /// View.onAppear 入口。首次进入执行 loadInitial,后续切 tab 来回不再重置。
    func loadInitialIfNeeded() async {
        guard !hasLoadedOnce else { return }
        hasLoadedOnce = true
        await loadFilters()
        await loadInitial()
    }

    /// 全量重置 + 拉首屏。filter 切换时也走这里。
    func loadInitial() async {
        // 入口 +1 generation —— 在飞的 loadMore 看到不一致会丢弃自己的结果
        requestGeneration += 1
        isLoading = true
        defer { isLoading = false }
        messages = []
        nextCursor = nil
        hasMore = true
        // 切过滤后,清掉旧 selectedMessage(它的 detail 可能已经不符合新 filter)
        // 留给 selectMessage 重新拉;但保持 UI 状态不抖
        if let sm = selectedMessage, !messages.contains(where: { $0.id == sm.id }) {
            selectedMessage = nil
        }
        do {
            let result = try await repository.list(
                cursor: nil, limit: 20, filter: currentFilter
            )
            // SQL 是 DESC(最新优先),UI 要的是 ASC(最旧在最上、最新在最下)——
            // 这是聊天 App 的标准顺序。reverse() 把 array 翻成 [oldest, ..., newest]。
            messages = result.items.reversed()
            // nextCursor 取「最后一条」,但 last 现在是「最新的」,所以 cursor
            // 还是最新的 createdAt。下次 loadMore 会 `WHERE created_at < cursor`
            // 拿到「比最新还旧」的那页,正确。
            nextCursor = result.items.last?.createdAt
            hasMore = result.hasMore
            // 同步刷月度 timeline
            await reloadMonthlyTimeline()
            // 加载完 → 默认滚到底部(让用户落在最新消息)
            scrollToBottomPending = true
        } catch let e as RepositoryError {
            errorMessage = e.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 向上滚到接近顶部时触发 —— 拉更早消息,拼到 messages 数组头部。
    ///
    /// `restoreAnchor`:View 在触发那一刻记录的「viewport 顶部 message 的 id」,
    /// 用于 prepend 完成后 scrollTo 该 id 恢复视口(对齐 vue 端 tryRestoreScroll)。
    func loadMore(restoreAnchor: Int? = nil) async {
        guard !isLoading, hasMore, !dateJumpPending, let cursor = nextCursor else { return }
        // 200ms debounce:防止 LazyVStack 复用 marker view 重复 onAppear
        if let last = lastLoadMoreAt, Date().timeIntervalSince(last) < 0.2 { return }
        let myGen = requestGeneration
        lastLoadMoreAt = Date()
        // 把 anchor 写给 View,等 messages.count 变化时消费
        prependedPendingAnchor = restoreAnchor
        isLoading = true
        defer { isLoading = false }
        do {
            let result = try await repository.list(
                cursor: cursor, limit: 20, filter: currentFilter
            )
            // 期间 generation 变了(切过滤 / 日期跳转)→ 丢弃结果
            guard myGen == requestGeneration else { return }
            // 续翻返回「比 cursor 更早」的消息(DESC),需要 reverse 成 ASC,
            // 然后 prepend 到现有 messages 头部(消息[0] 是最旧的)。
            // 注:scroll position preservation(用户看到的那条不跳动)由 View 层
            // 处理 — VM 只负责正确的数组顺序 + 把 anchor 传出去。
            messages.insert(contentsOf: result.items.reversed(), at: 0)
            nextCursor = result.nextCursor
            hasMore = result.hasMore
        } catch let e as RepositoryError {
            errorMessage = e.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// View 在 messages.count 变化时消费一次,取走 prepend anchor 用于 scrollTo。
    /// consume 语义:返回后清空,避免下次无 prepend 的 messages 变化误触 scrollTo。
    func consumePrependedPendingAnchor() -> Int? {
        let v = prependedPendingAnchor
        prependedPendingAnchor = nil
        return v
    }

    // MARK: - 过滤切换

    /// 三选一互斥:点 tag 清 actor + issue,反之亦然。
    /// kind: .tag / .actor / .issue;`id == nil` 表示清除该类。
    func selectFilter(kind: FilterKind, id: Int?) async {
        // 入口 +1 generation;在飞的 loadMore 会丢弃自己的结果
        requestGeneration += 1
        switch kind {
        case .tag:
            selectedTagId = id
            if id != nil {
                selectedActorId = nil
                selectedIssueId = nil
            }
        case .actor:
            selectedActorId = id
            if id != nil {
                selectedTagId = nil
                selectedIssueId = nil
            }
        case .issue:
            selectedIssueId = id
            if id != nil {
                selectedTagId = nil
                selectedActorId = nil
            }
        }
        await loadInitial()
    }

    // MARK: - 选中消息

    /// 点击消息卡:从 messages 数组里取摘要 → 拉 detail(actor / 全量 media_items / tags)。
    func selectMessage(id: Int) async {
        // 先在 messages 数组里找到占位 summary(已经有 actor / media_count)
        guard let summary = messages.first(where: { $0.id == id }) else { return }
        // 立刻用 summary 占位 detail,避免「点击 - 加载」空白期
        selectedMessage = summary
        selectedMessageLoading = true
        do {
            if let full = try await repository.fetchMessageDetail(id: id) {
                // 防止 await 期间用户又点了别的消息
                if selectedMessage?.id == id {
                    selectedMessage = full
                }
            }
        } catch {
            // detail 拉取失败时,保留 summary 占位
        }
        selectedMessageLoading = false
    }

    /// 关闭 detail 面板。
    func clearSelectedMessage() {
        selectedMessage = nil
    }

    // MARK: - 日期跳转

    /// DateScrubber 拖到某日 → 拉该日的最新消息(取该日 23:59:59.999999 作为 cursor)。
    /// 之后让 view 滚到该日首条消息在 messages 数组中的位置。
    func scrollToDate(year: Int, month: Int, day: Int) async {
        // 入口 +1 generation;在飞的 loadMore 会丢弃自己的结果
        requestGeneration += 1
        // 日期跳转后 ~500ms 内抑制 prefetch —— 否则 cursor = endOfDay 之下会跨日期
        // 边界拉到不该出现的更早消息。
        dateJumpPending = true
        dateJumpClearTask?.cancel()
        dateJumpClearTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 500_000_000)
            guard !Task.isCancelled else { return }
            await MainActor.run { self?.dateJumpPending = false }
        }
        var comp = DateComponents()
        comp.year = year; comp.month = month; comp.day = day
        comp.hour = 23; comp.minute = 59; comp.second = 59
        let endOfDay = Calendar.current.date(from: comp) ?? Date()
        let cursor = MessageCursor.encode(endOfDay)
        isLoading = true
        defer { isLoading = false }
        do {
            let result = try await repository.list(
                cursor: cursor, limit: 20, filter: currentFilter
            )
            // 与 loadInitial 同款:reverse DESC → ASC,保持 [oldest, ..., newest] 顺序
            messages = result.items.reversed()
            nextCursor = result.items.last?.createdAt
            hasMore = result.hasMore
            // 滚到该日首条 = messages 数组中第一条(date >= 该日 0 点的)
            var targetComp = DateComponents()
            targetComp.year = year; targetComp.month = month; targetComp.day = day
            let dayStart = Calendar.current.date(from: targetComp) ?? Date()
            pendingScrollToDateAnchor = dayStart
        } catch let e as RepositoryError {
            errorMessage = e.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// View 层在 messages 渲染完后,如果有 pendingScrollToDateAnchor 就滚到对应消息位置。
    func consumePendingScrollToDateAnchor() -> Date? {
        let v = pendingScrollToDateAnchor
        pendingScrollToDateAnchor = nil
        return v
    }

    /// 类似:loadInitial 完后默认滚到底部。
    func consumeScrollToBottomPending() -> Bool {
        let v = scrollToBottomPending
        scrollToBottomPending = false
        return v
    }

    // MARK: - 搜索 debounce

    /// 300ms debounce 触发 loadInitial —— 避免每键一次 SQL。
    func scheduleDebouncedSearch() {
        debounceTask?.cancel()
        debounceTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 300_000_000)
            guard !Task.isCancelled, let self else { return }
            await self.loadInitial()
        }
    }

    // MARK: - 内部

    @Published private(set) var scrollToBottomPending: Bool = false
    private var pendingScrollToDateAnchor: Date? = nil

    /// 拉侧栏过滤条目(并发跑三个 fetch)。
    private func loadFilters() async {
        do {
            let (tags, actors, issues) = try await repository.fetchFilters()
            availableTags = tags
            availableActors = actors
            availableIssues = issues
        } catch {
            // 侧栏条目拉取失败不阻塞 feed;非致命
        }
    }

    /// 月度 timeline:用当前 filter 调 MessageRepository.monthlyDayCount。
    private func reloadMonthlyTimeline() async {
        // 取当前月(year/month 用 latest message 的日期;没有时用今天)
        let now = Date()
        let year = Calendar.current.component(.year, from: now)
        let month = Calendar.current.component(.month, from: now)
        do {
            monthlyDayCount = try await repository.monthlyDayCount(
                year: year, month: month, filter: currentFilter
            )
        } catch {
            monthlyDayCount = []
        }
    }
}

// MARK: - 辅助枚举

extension MessagesViewModel {
    enum FilterKind {
        case tag, actor, issue
    }
}
