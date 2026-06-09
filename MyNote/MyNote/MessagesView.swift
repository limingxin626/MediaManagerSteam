//
//  MessagesView.swift
//  MyNote
//
//  消息流主视图 —— Mac 端独立 UX:顺向 feed(最新在顶 / 向下滚加载更早)。
//
//  与 vue 端 IM 风格(最新在底 / 向上滚加载更早)**不一致**,理由:
//    SwiftUI 的 LazyVStack 在反向 feed 场景下存在多个不稳定点 ——
//    末尾空 view 首屏不渲染、ScrollViewProxy 对未实例化 id 的强制布局
//    契约对 LazyVStack 不可靠、prepend 时视口恢复抖动等。改成顺向后
//    就是 SwiftUI 的标准模式(Twitter / Mastodon 风格 feed),无需任何
//    程序化 scroll 协调:
//      - 初始位置 = 自然顶部 = messages[0] = 最新消息(默认行为)
//      - 向下滚到接近底部 → onAppear 触发 loadMore → append → 标准模式
//      - prepend / restoreAnchor / scrollToBottom 全部不需要
//
//  结构:
//
//    ┌────────────────────────────────────────────────────────┐
//    │   顶栏(toolbar):标题 + 搜索 + 星标 toggle + 刷新 +   │
//    │                    DateScrubber / 过滤 dropdown        │
//    ├──────────┬─────────────────────────────────────────────┤
//    │          │                                             │
//    │ Filter   │   MessagesList (LazyVStack,顺向)          │
//    │ Sidebar  │   ┌─────────────────────────────┐           │
//    │  (tags/  │   │ MessageCard(最新)           │           │
//    │  actors/ │   │   - actor + 时间             │           │
//    │  issues) │   │   - 正文                     │           │
//    │          │   │   - tag chips                │           │
//    │          │   │   - media grid               │           │
//    │          │   │   - 底部条(星标/媒体数/id)   │           │
//    │          │   └─────────────────────────────┘           │
//    │          │   ...                                       │
//    │          │   ┌─────────────────────────────┐           │
//    │          │   │ MessageCard(更早)           │           │
//    │          │   └─────────────────────────────┘           │
//    │          │   ↓ "加载更早…" / "已经是最早" sentinel    │
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

        ZStack(alignment: .top) {
            HStack(spacing: 0) {
                if showSidebar {
                    FilterSidebar(viewModel: viewModel)
                        .transition(.opacity)
                }

                feedPane
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
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

    // MARK: - 消息列表(顺向 feed)
    //
    // 标准 SwiftUI 模式:
    //   - ScrollView 默认从顶部开始渲染 → messages[0] 在视口顶 → 用户看到最新
    //   - 距离数组末尾第 N 条放一个不可见 marker,onAppear 时 loadMore →
    //     append 到末尾。新内容加在用户视口"下方之外",不抖动当前位置。
    //
    // 不再需要的(顺向模式天然规避了):
    //   - ScrollViewReader / proxy.scrollTo
    //   - bottom-anchor 空 view
    //   - frame 跟踪 + topAnchor 计算 + PreferenceKey
    //   - prepend 视口恢复 anchor
    //   - scrollToBottomPending 标志位

    private var messagesScrollView: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 12) {
                ForEach(Array(viewModel.messages.enumerated()), id: \.element.id) { idx, msg in
                    MessageCard(message: msg)
                    // prefetch marker:在距离末尾第 10 条 message 之后挂一个
                    // 不可见 trigger,LazyVStack 渲染到这里时 onAppear → loadMore。
                    // 这是 SwiftUI 顺向无限滚动的标准用法,无 reverse 模式那些坑。
                    if idx == prefetchTriggerIndex {
                        Color.clear
                            .frame(height: 1)
                            .onAppear { handlePrefetchTrigger() }
                    }
                }
                loadMoreSentinel
            }
            .padding(16)
        }
    }

    /// 在「距离末尾倒数第 10 条」**之后**挂 trigger。
    /// PREFETCH_DISTANCE = 10:还剩 10 条没看到时就预拉下一页,与 vue 一致。
    /// 当 count <= 10 时:trigger 落到第 0 条之后 = 视口顶,首屏自然就要 prefetch
    /// (符合预期:消息不够 10 条时,如果还有更多就立即拉下一页)。
    private var prefetchTriggerIndex: Int {
        max(0, viewModel.messages.count - 1 - 10)
    }

    /// prefetch marker onAppear 触发:异步 loadMore。
    /// VM 内部 200ms debounce + dateJumpPending + isLoading 守门防抖。
    private func handlePrefetchTrigger() {
        guard viewModel.hasMore, !viewModel.dateJumpPending else { return }
        Task { await viewModel.loadMore() }
    }

    /// 底部 sentinel:loading 时显示 spinner,已无更多时显示「已经是最早」。
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
