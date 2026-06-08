//
//  MessagesView.swift
//  MyNote
//
//  消息流主视图 —— 与 vue 端 Message.vue 同构的只读浏览能力。
//
//  结构:
//
//    ┌────────────────────────────────────────────────────────┐
//    │   顶栏(toolbar):标题 + 搜索 + 星标 toggle + 刷新 +   │
//    │                    DateScrubber / 过滤 dropdown        │
//    ├──────────┬─────────────────────────────────────────────┤
//    │          │                                             │
//    │ Filter   │   MessagesList (LazyVStack)                │
//    │ Sidebar  │   ┌─────────────────────────────┐           │
//    │  (tags/  │   │ MessageCard                 │           │
//    │  actors/ │   │   - actor + 时间             │           │
//    │  issues) │   │   - 正文                     │           │
//    │          │   │   - tag chips                │           │
//    │          │   │   - media grid               │           │
//    │          │   │   - 底部条(星标/媒体数/id)   │           │
//    │          │   └─────────────────────────────┘           │
//    │          │   ...                                       │
//    │          │              ┌─────────────────────┐        │
//    │          │              │ MessageDetailPane   │ (有选中时)
//    │          │              │  - 完整 actor+正文  │        │
//    │          │              │  - 全量 media grid  │        │
//    │          │              │  - ESC / × 关闭     │        │
//    │          │              └─────────────────────┘        │
//    └──────────┴─────────────────────────────────────────────┘
//
//  状态保留:ContentView 持 @StateObject(MessagesViewModel),切 tab 来回不丢。
//  写操作:零(本 change 范围内不暴露任何 mutation API)。
//

import SwiftUI

struct MessagesView: View {
    @ObservedObject var viewModel: MessagesViewModel

    /// 主窗口可用宽度(用于窄屏检测:决定 detail pane 是否显示 / sidebar 折叠)
    @State private var containerWidth: CGFloat = 1200

    /// 媒体预览 destination —— 推入 NavigationPath 打开 MediaDetailView。
    @State private var navigationPath = NavigationPath()
    /// 当前正在预览的媒体数组(从某条 message 拿到的 mediaItems) + 起始 index。
    @State private var previewMediaList: [Media] = []
    @State private var previewIndex: Int = 0
    @State private var previewIndexBox: IndexBox? = nil

    // MARK: - Prefetch 状态

    /// 当前 viewport 内「最顶部」那条 message 的 id —— 触发 loadMore 时把
    /// 它作为 `restoreAnchor` 传给 VM,prepend 完成后 scrollTo 恢复视口。
    /// 计算来源:MessageCard 报上来的 frame 字典 + ScrollView 当前 contentOffset.y。
    @State private var topAnchorMessageId: Int? = nil
    /// 各 message 的 frame.minY(name coordinate space = "feed")字典。
    /// 每条 message card 渲染时通过 PreferenceKey 报上来,scroll 时用于找
    /// 「在视口顶部第一条」的 id。
    @State private var messageFrames: [Int: CGFloat] = [:]
    /// ScrollView 当前 contentOffset(同步到 `@State` 供 `onScrollGeometryChange` 使用)。
    @State private var currentScrollY: CGFloat = 0
    @State private var currentViewportHeight: CGFloat = 0

    var body: some View {
        GeometryReader { geo in
            NavigationStack(path: $navigationPath) {
                content(for: geo.size.width)
                    .navigationTitle(AppTab.messages.title)
                    .navigationDestination(for: MessagesPreviewDestination.self) { dest in
                        MediaDetailView(
                            mediaList: dest.mediaList,
                            currentIndex: dest.currentIndexBinding ?? .constant(dest.startIndex),
                            hasMore: false,
                            onNeedMore: { /* 单消息内已加载全部媒体,无需翻页 */ },
                            onClose: { closePreview() }
                        )
                    }
                    .toolbar { toolbarContent }
            }
            .onAppear { containerWidth = geo.size.width }
            .onChange(of: geo.size.width) { _, new in containerWidth = new }
        }
    }

    // MARK: - 主内容布局

    @ViewBuilder
    private func content(for width: CGFloat) -> some View {
        let showSidebar = width >= 800
        let showDetail = width >= 800 && viewModel.selectedMessage != nil

        ZStack(alignment: .top) {
            HStack(spacing: 0) {
                if showSidebar {
                    FilterSidebar(viewModel: viewModel)
                        .transition(.opacity)
                }

                feedPane
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                if showDetail, let message = viewModel.selectedMessage {
                    Divider()
                    MessageDetailPane(
                        message: message,
                        isLoading: viewModel.selectedMessageLoading,
                        onClose: { viewModel.clearSelectedMessage() },
                        onMediaPreview: { index in openPreview(message: message, startIndex: index) }
                    )
                    .frame(idealWidth: 420, maxWidth: 600)
                    .transition(.move(edge: .trailing).combined(with: .opacity))
                }
            }

            // 错误浮层
            if let err = viewModel.errorMessage {
                errorBanner(err)
            }
        }
        .onAppear {
            Task { await viewModel.loadInitialIfNeeded() }
        }
        .onChange(of: viewModel.searchText) { _, _ in
            viewModel.scheduleDebouncedSearch()
        }
    }

    // MARK: - feed pane

    @ViewBuilder
    private var feedPane: some View {
        ZStack {
            if viewModel.isLoading && viewModel.messages.isEmpty {
                // 首屏 loading
                VStack {
                    Spacer()
                    ProgressView()
                    Spacer()
                }
            } else if !viewModel.isLoading && viewModel.messages.isEmpty && viewModel.errorMessage == nil {
                // 空状态
                VStack(spacing: 12) {
                    Spacer()
                    Image(systemName: AppTab.messages.systemImage)
                        .font(.system(size: 56))
                        .foregroundColor(.secondary.opacity(0.5))
                    Text("暂无消息")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.secondary)
                    Text("数据库里还没有任何消息,或者当前过滤条件下没有命中")
                        .font(.system(size: 12))
                        .foregroundColor(.secondary.opacity(0.7))
                    Spacer()
                }
            } else {
                messagesScrollView
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(nsColor: .windowBackgroundColor))
    }

    private var messagesScrollView: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    // 顶部 status:只是视觉占位,「加载更早…spinner / 已经是最早」
                    // 文本;不再承担触发职责。触发交给下面的 prefetch marker。
                    loadMoreSentinel
                        .id("top-sentinel")
                    ForEach(viewModel.messages.indices, id: \.self) { idx in
                        let msg = viewModel.messages[idx]
                        // prefetch marker:在距离顶部第 10 条 message 之前,
                        // 不可见 Color.clear 触发器。
                        // 不加 .id(...) —— 让 SwiftUI 用默认 identity,这样 prepend
                        // 后旧 marker view 被销毁,新 marker view 实例化 → onAppear 重触发。
                        if idx == prefetchIndex {
                            Color.clear
                                .frame(height: 1)
                                .onAppear { handlePrefetchTrigger() }
                        }
                        MessageCard(
                            message: msg,
                            isSelected: viewModel.selectedMessage?.id == msg.id,
                            onCardClick: {
                                Task { await viewModel.selectMessage(id: msg.id) }
                            },
                            onMediaClick: { _ in
                                // feed 内点媒体不直接进 preview(对齐 vue 端 Message.vue 的行为)
                                // 而是先选中消息 → 详情面板里再点媒体才进 preview
                                Task { await viewModel.selectMessage(id: msg.id) }
                            }
                        )
                        .id(msg.id)
                        // 报告自己的 frame.minY(name space: "feed"),让 View 计算 topAnchor
                        .background(
                            GeometryReader { cardGeo in
                                Color.clear
                                    .preference(
                                        key: MessageFramePreferenceKey.self,
                                        value: [msg.id: cardGeo.frame(in: .named("feed")).minY]
                                    )
                            }
                        )
                    }
                    // 底部锚点 —— scrollToBottom 时跳到这里,让用户落在最新消息。
                    Color.clear
                        .frame(height: 1)
                        .id("bottom-anchor")
                }
                .padding(16)
            }
            .coordinateSpace(name: "feed")
            .onPreferenceChange(MessageFramePreferenceKey.self) { frames in
                // 各 message 自己报的 frame 字典
                self.messageFrames = frames
            }
            .onScrollGeometryChange(for: ScrollGeometrySnapshot.self) { geo in
                ScrollGeometrySnapshot(
                    contentOffsetY: geo.contentOffset.y,
                    containerHeight: geo.containerSize.height
                )
            } action: { _, snapshot in
                // 同步 scrollTop + viewportHeight,触发 topAnchor 重算
                self.currentScrollY = snapshot.contentOffsetY
                self.currentViewportHeight = snapshot.containerHeight
                self.topAnchorMessageId = computeTopmostMessageId()
            }
            // 初次加载完成 → 滚到底部(让用户落在最新消息)
            // 后续 loadMore 完成 → scrollTo anchor 恢复视口
            .onChange(of: viewModel.messages.count) { _, _ in
                if viewModel.consumeScrollToBottomPending() {
                    DispatchQueue.main.async {
                        proxy.scrollTo("bottom-anchor", anchor: .bottom)
                    }
                } else if let anchor = viewModel.consumePrependedPendingAnchor(),
                          viewModel.messages.contains(where: { $0.id == anchor }) {
                    DispatchQueue.main.async {
                        proxy.scrollTo(anchor, anchor: .top)
                    }
                }
            }
        }
    }

    /// PREFETCH_DISTANCE = 10 —— 与 vue 端 `Math.min(10, els.length - 1)` 对齐。
    /// 当 count < 10 时,marker 落在最后一条 message 之前(此时它就是第 N=count 条)。
    private var prefetchIndex: Int {
        max(0, min(10, viewModel.messages.count - 1))
    }

    /// 计算当前 viewport 顶部那条 message 的 id。
    /// 算法:`messageFrames` 中,`frame.minY >= scrollTop` 的最小值对应的 id。
    /// 找不到时返回 nil(用户滚到列表上方空白处)。
    private func computeTopmostMessageId() -> Int? {
        guard !messageFrames.isEmpty else { return nil }
        // 视口顶部容差 1pt,避免 cell 顶部正好卡在 scrollTop 上时算到下一条
        let threshold = currentScrollY + 1
        return messageFrames
            .filter { $0.value >= threshold }
            .min(by: { $0.value < $1.value })?
            .key
    }

    /// prefetch marker onAppear 触发:把当前 topAnchor id 传给 VM,异步 loadMore。
    /// VM 内部 200ms debounce + dateJumpPending + isLoading 守门防抖。
    private func handlePrefetchTrigger() {
        guard viewModel.hasMore, !viewModel.dateJumpPending else { return }
        let anchor = topAnchorMessageId
        Task { await viewModel.loadMore(restoreAnchor: anchor) }
    }

    /// 顶部 status:纯视觉占位条(显示「加载更早…」spinner /「已经是最早」),
    /// 触发职责已迁到 prefetch marker(onAppear)。
    @ViewBuilder
    private var loadMoreSentinel: some View {
        HStack(spacing: 6) {
            if viewModel.isLoading && !viewModel.messages.isEmpty {
                ProgressView().controlSize(.small)
                Text("加载更早的消息…")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            } else if !viewModel.hasMore && !viewModel.messages.isEmpty {
                Text("已经是最早的消息了")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary.opacity(0.6))
            } else {
                Color.clear.frame(height: 1)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 4)
    }

    // MARK: - 错误浮层

    private func errorBanner(_ message: String) -> some View {
        VStack {
            HStack {
                Text(message)
                    .font(.system(size: 12))
                    .foregroundColor(.red)
                Spacer()
                Button(action: { viewModel.errorMessage = nil }) {
                    Image(systemName: "xmark")
                        .font(.system(size: 10))
                }
                .buttonStyle(.plain)
                .foregroundColor(.red)
            }
            .padding(8)
            .background(Color.red.opacity(0.1))
            .cornerRadius(6)
            .padding(.horizontal, 12)
            .padding(.top, 8)
            Spacer()
        }
    }

    // MARK: - 顶栏(toolbar)

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .principal) {
            HStack(spacing: 8) {
                // 搜索框
                HStack(spacing: 4) {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.secondary)
                    TextField("搜索消息...", text: $viewModel.searchText)
                        .textFieldStyle(.plain)
                        .frame(width: 200)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.gray.opacity(0.12))
                .clipShape(RoundedRectangle(cornerRadius: 6))

                // 星标 toggle(仅看收藏)
                Button {
                    viewModel.starredOnly.toggle()
                    Task { await viewModel.loadInitial() }
                } label: {
                    Image(systemName: viewModel.starredOnly ? "star.fill" : "star")
                        .foregroundColor(viewModel.starredOnly ? .orange : .secondary)
                }
                .help(viewModel.starredOnly ? "显示全部" : "仅看收藏")

                // 刷新
                Button {
                    Task { await viewModel.loadInitial() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .help("刷新")
            }
        }

        ToolbarItem(placement: .primaryAction) {
            HStack(spacing: 8) {
                // 当前过滤徽章(有任一 filter 选中时显示)
                if viewModel.selectedTagId != nil
                    || viewModel.selectedActorId != nil
                    || viewModel.selectedIssueId != nil {
                    HStack(spacing: 4) {
                        Text(currentFilterLabel)
                            .font(.system(size: 11))
                            .foregroundColor(.accentColor)
                        Button {
                            Task { await viewModel.selectFilter(kind: .tag, id: nil) }
                        } label: {
                            Image(systemName: "xmark.circle.fill")
                                .font(.system(size: 11))
                        }
                        .buttonStyle(.plain)
                        .foregroundColor(.secondary)
                    }
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.accentColor.opacity(0.10))
                    .clipShape(Capsule())
                }

                // 窄屏 fallback
                if containerWidth < 800 {
                    FilterMenuCompact(viewModel: viewModel)
                }

                // DateScrubber(仅 timeline 非空时)
                if !viewModel.monthlyDayCount.isEmpty {
                    DateScrubber(
                        timeline: viewModel.monthlyDayCount as! [TimelineEntry],
                        minDate: timelineMinDate,
                        maxDate: timelineMaxDate,
                        currentDate: timelineMinDate,
                        onJump: { _ in },
                        onJumpFinal: { date in
                            Task { await viewModel.scrollToDate(year: yearOf(date), month: monthOf(date), day: dayOf(date)) }
                        }
                    )
                    .frame(width: 60)
                }
            }
        }
    }

    private var currentFilterLabel: String {
        if let id = viewModel.selectedTagId,
           let tag = viewModel.availableTags.first(where: { $0.id == id }) {
            return "#\(tag.name)"
        }
        if let id = viewModel.selectedActorId {
            if id == 0 { return "无演员" }
            if let actor = viewModel.availableActors.first(where: { $0.id == id }) {
                return actor.name
            }
        }
        if let id = viewModel.selectedIssueId {
            if id == 0 { return "无 issue" }
            if let issue = viewModel.availableIssues.first(where: { $0.id == id }) {
                return issue.title
            }
        }
        return ""
    }

    private var timelineMinDate: Date {
        // 取该月最早一天
        guard let first = viewModel.monthlyDayCount.last else { return Date() }
        var comp = DateComponents()
        comp.year = first.year; comp.month = first.month; comp.day = first.day
        return Calendar.current.date(from: comp) ?? Date()
    }

    private var timelineMaxDate: Date {
        guard let first = viewModel.monthlyDayCount.first else { return Date() }
        var comp = DateComponents()
        comp.year = first.year; comp.month = first.month; comp.day = first.day
        comp.hour = 23; comp.minute = 59; comp.second = 59
        return Calendar.current.date(from: comp) ?? Date()
    }

    private func yearOf(_ d: Date) -> Int { Calendar.current.component(.year, from: d) }
    private func monthOf(_ d: Date) -> Int { Calendar.current.component(.month, from: d) }
    private func dayOf(_ d: Date) -> Int { Calendar.current.component(.day, from: d) }

    // MARK: - 媒体预览

    private func openPreview(message: Message, startIndex: Int) {
        let mediaList = message.mediaItems.map { $0.asMedia() }
        guard !mediaList.isEmpty else { return }
        let safe = max(0, min(startIndex, mediaList.count - 1))
        let box = IndexBox(value: safe)
        let binding = Binding<Int>(get: { box.value }, set: { box.value = $0 })
        let dest = MessagesPreviewDestination(
            mediaList: mediaList,
            startIndex: safe,
            currentIndexBinding: binding
        )
        previewIndexBox = box
        // 设置导航栏标题
        if let text = message.text, !text.isEmpty {
            PreviewTitle.shared.title = String(text.prefix(30))
        } else {
            PreviewTitle.shared.title = "消息 #\(message.id)"
        }
        navigationPath.append(dest)
    }

    private func closePreview() {
        if let box = previewIndexBox {
            previewIndex = box.value
        }
        previewIndexBox = nil
        navigationPath.removeLast()
    }
}

// MARK: - 预览 destination

struct MessagesPreviewDestination: Hashable {
    let mediaList: [Media]
    let startIndex: Int
    let currentIndexBinding: Binding<Int>?

    static func == (lhs: MessagesPreviewDestination, rhs: MessagesPreviewDestination) -> Bool {
        // 比较时不考虑 binding(它本身是引用),只看 list 指针 + startIndex
        lhs.mediaList.map { $0.id } == rhs.mediaList.map { $0.id }
            && lhs.startIndex == rhs.startIndex
    }

    func hash(into hasher: inout Hasher) {
        for m in mediaList { hasher.combine(m.id) }
        hasher.combine(startIndex)
    }
}

// MARK: - Prefetch 支撑类型

/// `onScrollGeometryChange` 拿到的快照(只要 contentOffset.y + containerSize.height,
/// 不需要 contentSize/contentInsets 等无关字段,避免不必要的 diff 触发)。
struct ScrollGeometrySnapshot: Equatable {
    let contentOffsetY: CGFloat
    let containerHeight: CGFloat
}

/// 各 MessageCard 报告自己 frame.minY 的 PreferenceKey。
/// value 是 `[messageId: minY]` 字典,每次有 card 出现 / 消失 / 移动都会触发
/// `onPreferenceChange`,View 用最新字典算 topmost message。
struct MessageFramePreferenceKey: PreferenceKey {
    typealias Value = [Int: CGFloat]
    static var defaultValue: [Int: CGFloat] = [:]

    static func reduce(value: inout [Int: CGFloat], nextValue: () -> [Int: CGFloat]) {
        // 每张 card 报自己一个 entry,reduce 时取后面的(nextValue)覆盖 —— 这样
        // 已经不在视口里的 card 不会"卡住"它的旧 frame(因为它的 .background
        // GeometryReader 会重渲染并 report 新的 0/offscreen 位置)。
        value = nextValue()
    }
}
