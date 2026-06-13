//
//  MessagesViewModel.swift
//  MyNote
//
//  消息流数据 / 状态 / 分页 / 过滤 —— Mac 端独立 UX:
//
//    1. 数组顺序 DESC = 最新在 messages[0],最旧在 messages[count-1]。
//       与 SQL 的 `ORDER BY created_at DESC, id DESC` 自然对齐,不再 reverse;
//       UI 侧也由顶到底显示「最新 → 最旧」,与 Twitter/微博 feed 一致。
//    2. 抛弃 vue 端「IM 风格 (最新在底)+ 反向上拉加载」—— 在 SwiftUI
//       LazyVStack 上无法稳定实现(末尾空 view 首屏不渲染、ScrollViewProxy
//       对未实例化 id 的强制布局契约对 LazyVStack 不可靠、prepend 时视口
//       恢复抖动等)。Mac 端取顺向 = SwiftUI 的标准模式 = 稳定。
//    3. 单一数据源:messages: [Message] 是 feed 全量(已加载的),分页
//       loadMore / selectFilter 都基于这个数组 + nextCursor。
//    4. 状态保留:ContentView 以 @StateObject 持有本 VM,切 tab 来回不丢。
//    5. 写操作:文字 / tag / 星标三个字段已开放,走 APIClient → backend PATCH。
//       媒体增删 / 合并 / 拆分 / 删除消息仍未开放。
//    6. 不再持有 selectedMessage —— 详情面板已下线,点击卡是 no-op。
//

import Foundation
import Combine

@MainActor
final class MessagesViewModel: ObservableObject {

    // MARK: - Published 状态

    /// feed 当前已加载的消息列表(DESC:最新在 [0],最旧在 [count-1])。
    @Published private(set) var messages: [Message] = []

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

    // 月度 timeline(DateScrubber 渲染所需)
    @Published private(set) var monthlyDayCount: [TimelineEntry] = []

    // 过滤侧栏条目
    @Published private(set) var availableTags: [Tag] = []
    @Published private(set) var availableActors: [Actor] = []
    @Published private(set) var availableIssues: [Issue] = []

    /// scrollToDate 之后 ~500ms 内为 true。View 在 prefetch marker 触发时
    /// 检查它,避免跨日期边界拉到不该出现的旧消息。
    @Published private(set) var dateJumpPending: Bool = false

    // MARK: - 依赖

    private let repository: MessageRepository
    private let apiClient: APIClient

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

    init(repository: MessageRepository = MessageRepository(),
         apiClient: APIClient = APIClient()) {
        self.repository = repository
        self.apiClient = apiClient
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
        do {
            let result = try await repository.list(
                cursor: nil, limit: 20, filter: currentFilter
            )
            // SQL 已是 DESC(最新优先),直接用;UI 顶到底显示「最新 → 最旧」。
            messages = result.items
            nextCursor = result.nextCursor
            hasMore = result.hasMore
            // 同步刷月度 timeline
            await reloadMonthlyTimeline()
        } catch let e as RepositoryError {
            errorMessage = e.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 向下滚到接近底部时触发 —— 拉更早消息,append 到 messages 数组末尾。
    /// SwiftUI LazyVStack 顺向 append 是标准模式,无需视口恢复 anchor:
    /// 用户视口位置在数组中间,新内容加在底部之外,SwiftUI 不动 contentOffset。
    func loadMore() async {
        guard !isLoading, hasMore, !dateJumpPending, let cursor = nextCursor else { return }
        // 200ms debounce:防止 LazyVStack 复用 marker view 重复 onAppear
        if let last = lastLoadMoreAt, Date().timeIntervalSince(last) < 0.2 { return }
        let myGen = requestGeneration
        lastLoadMoreAt = Date()
        isLoading = true
        defer { isLoading = false }
        do {
            let result = try await repository.list(
                cursor: cursor, limit: 20, filter: currentFilter
            )
            // 期间 generation 变了(切过滤 / 日期跳转)→ 丢弃结果
            guard myGen == requestGeneration else { return }
            messages.append(contentsOf: result.items)
            nextCursor = result.nextCursor
            hasMore = result.hasMore
        } catch let e as RepositoryError {
            errorMessage = e.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
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

    // MARK: - 日期跳转

    /// DateScrubber 拖到某日 → 拉该日的最新消息(取该日 23:59:59.999999 作为 cursor)。
    /// 拉回来后用户视口在顶部 = 该日最新一条,自然往下滚就是看历史。
    func scrollToDate(year: Int, month: Int, day: Int) async {
        // 入口 +1 generation;在飞的 loadMore 会丢弃自己的结果
        requestGeneration += 1
        // 日期跳转后 ~500ms 内抑制 prefetch —— 否则刚 reset 完 marker 进视口
        // 会立刻拉下一页,污染用户预期。
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
            // 同 loadInitial:DESC 直接用,最新在 [0]
            messages = result.items
            nextCursor = result.nextCursor
            hasMore = result.hasMore
        } catch let e as RepositoryError {
            errorMessage = e.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
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

    // MARK: - 编辑 / 写操作
    //
    // 走 backend HTTP(PATCH /messages/{id})—— Mac 端 GRDB 是 read-only,写
    // 必须经过后端,以复用 message_service 里的 #hashtag 解析、SyncLog 落表
    // 等服务层逻辑。
    //
    // 拿到 backend 返回的最新 Message 后,在 messages 数组里就地替换 ——
    // Message 是 struct 全 `let`,部分字段改不动,只能整条换。

    /// 提交「编辑态」保存:可同时改 text 和 tag。
    /// - tagIds 传 nil 表示不动 tag(后端按 text 里 #hashtag 重抽);传 [] 清空。
    /// - 成功后用返回值替换 messages[i],UI 自动重渲。
    /// - 失败设置 errorMessage,messages 不变(调用方仍处于编辑态,可重试)。
    /// - Returns: 是否成功(供 View 决定是否退出编辑态)。
    @discardableResult
    func commitEdit(messageId: Int, text: String?, tagIds: [Int]?) async -> Bool {
        do {
            let updated = try await apiClient.updateMessage(
                id: messageId, text: text, tagIds: tagIds, starred: nil
            )
            applyUpdated(updated)
            return true
        } catch let e as APIClient.APIError {
            errorMessage = e.errorDescription
            return false
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    /// 星标 toggle —— 乐观更新:先就地翻转 UI,失败再回滚 + errorMessage。
    /// 编辑态 / 只读态都可用,不进 commitEdit 缓冲区。
    func toggleStar(messageId: Int) async {
        guard let idx = messages.firstIndex(where: { $0.id == messageId }) else { return }
        let original = messages[idx]
        let newStar = !original.starred
        messages[idx] = replacing(original, starred: newStar)

        do {
            let updated = try await apiClient.updateMessage(
                id: messageId, text: nil, tagIds: nil, starred: newStar
            )
            applyUpdated(updated)
        } catch let e as APIClient.APIError {
            // 失败回滚
            if let i = messages.firstIndex(where: { $0.id == messageId }) {
                messages[i] = original
            }
            errorMessage = e.errorDescription
        } catch {
            if let i = messages.firstIndex(where: { $0.id == messageId }) {
                messages[i] = original
            }
            errorMessage = error.localizedDescription
        }
    }

    /// 在 messages 数组里用 id 找到对应项,整体替换。找不到不做事
    /// (例如用户在等待响应期间切了过滤,旧消息已不在 feed 中)。
    private func applyUpdated(_ msg: Message) {
        guard let idx = messages.firstIndex(where: { $0.id == msg.id }) else { return }
        messages[idx] = msg
    }

    /// 仅供 toggleStar 乐观更新用:克隆一条 Message,把 starred 换成新值,
    /// 其他字段照搬。Message 全 `let`,只能这样重建。
    private func replacing(_ msg: Message, starred: Bool) -> Message {
        Message(
            id: msg.id,
            text: msg.text,
            createdAt: msg.createdAt,
            updatedAt: msg.updatedAt,
            actorId: msg.actorId,
            actorName: msg.actorName,
            issueId: msg.issueId,
            issueTitle: msg.issueTitle,
            mediaCount: msg.mediaCount,
            starred: starred,
            mediaItems: msg.mediaItems,
            tags: msg.tags
        )
    }
}

// MARK: - 辅助枚举

extension MessagesViewModel {
    enum FilterKind {
        case tag, actor, issue
    }
}
