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

    /// 主窗口可用宽度,由 ContentView 顶层 GeometryReader 算出后传入。
    /// 只用于内容布局判断(决定 FilterSidebar 是否折叠);toolbar 已上提到
    /// ContentView,窄屏 fallback 在那一侧用同一个值判断,避免本 view 内
    /// 再嵌一层 GeometryReader 让 toolbar 与 ZStack 兄弟节点的 toolbar 重叠。
    let containerWidth: CGFloat

    /// NavigationStack 保留空跑 —— 维持 ContentView 上提 toolbar 的路由契约
    /// (每个 tab 自带 NavigationStack 以承接 navigationTitle / window title)。
    /// 预览不再走 navigationPath.append,改为 ZStack overlay(见 previewState)。
    @State private var navigationPath = NavigationPath()

    /// 媒体预览状态 —— 单一来源,nil 表示无预览,有值时 overlay 渲染 MediaDetailView。
    ///
    /// 之所以 overlay 而非 NavigationStack push:
    ///   1) push 后 SwiftUI 会重 layout 消息流的 LazyVStack,pop 回来时
    ///      标准 ScrollView 的滚动位置在 macOS 14 上恢复不稳定(已知 Apple
    ///      bug,FB13322236 / FB13455901)—— 用户感受为「关掉预览后列表回顶」。
    ///   2) push 同时让焦点链跨容器游走,关闭后下一次空格易误触发 toolbar /
    ///      sidebar 上的可聚焦元素 —— 用户感受为「再按空格打开了别的媒体」。
    /// overlay 模式下消息流 view 永不卸载 → 滚动位置由 SwiftUI 自然保留;
    /// 配合下面的 @FocusState feedFocused,焦点也显式收敛。
    @State private var previewState: PreviewState? = nil

    /// 消息流容器焦点 —— openPreview 时置 false 让 MediaDetailView 抢焦点,
    /// closePreview 时置 true 把焦点收回消息流,防止下一次按键被旁边的
    /// focusable 元素(toolbar 按钮 / sidebar chip)截胡。
    @FocusState private var feedFocused: Bool

    /// 预览当前索引 —— 用 @State 而非 PreviewState 内的引用包装,
    /// 这样 MediaDetailView 翻页改写时 SwiftUI 能正确追踪依赖、
    /// 持续触发 MessagesView 重算并把新值通过 $previewIndex 传回去。
    /// 打开预览时在 openPreview 内重置到 startIndex。
    @State private var previewIndex: Int = 0

    var body: some View {
        NavigationStack(path: $navigationPath) {
            ZStack {
                content(for: containerWidth)
                    .navigationTitle(AppTab.messages.title)

                if let state = previewState {
                    // .id(state.id) 强制每次打开都是全新 view —— 否则连续打开两条
                    // 不同消息的同一索引位置时,SwiftUI 会 reuse,内部 @State
                    // (AVPlayer / isFocused / chromeVisible / mouseMonitor)不会重置。
                    MediaDetailView(
                        mediaList: state.mediaList,
                        currentIndex: $previewIndex,
                        hasMore: false,
                        onNeedMore: { /* 单消息内已加载全部媒体,无需翻页 */ },
                        onClose: { closePreview() }
                    )
                    .id(state.id)
                    .background(Color(.windowBackgroundColor))
                    .transition(.opacity)
                    .zIndex(1)
                }
            }
            .animation(.easeInOut(duration: 0.18), value: previewState?.id)
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
                    MessageCard(message: msg, viewModel: viewModel) { mediaIndex in
                        openPreview(message: msg, startIndex: mediaIndex)
                    }
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
        // 容器级焦点 —— 让关闭预览时焦点有明确归宿,不再游走到 toolbar / sidebar
        // 上随便一个 focusable 元素。focusEffectDisabled 关掉系统蓝色 ring,
        // 因为消息流没有「选中某条」的可视态,ring 会显得突兀(参 MediaLibraryView)。
        .focusable(true)
        .focused($feedFocused)
        .focusEffectDisabled(true)
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
    //
    // toolbar 已上提到 ContentView,这里只提供工厂方法供其调用。改成 static
    // 是为了让 ContentView 不必持有 MessagesView 实例就能拼出 ToolbarContent;
    // 同时所有依赖都显式经 viewModel / containerWidth 入参,语义不会被隐式
    // 状态污染(原 toolbarContent 计算属性偷偷读 self.containerWidth 的写法
    // 已废)。`@ToolbarContentBuilder` 在 static func 上一样支持。

    @ToolbarContentBuilder
    static func messagesToolbar(viewModel: MessagesViewModel, containerWidth: CGFloat) -> some ToolbarContent {
        ToolbarItem(placement: .principal) {
            HStack(spacing: 8) {
                // 搜索框
                HStack(spacing: 4) {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.secondary)
                    // viewModel 是 class,$searchText 投影在 static 上下文里
                    // 不可用;手工构造 Binding 等价 —— ContentView 持有 @StateObject,
                    // 重渲染时 viewModel 引用稳定,Binding 闭包内的取值/赋值始终落在同一实例上。
                    TextField("搜索消息...", text: Binding(
                        get: { viewModel.searchText },
                        set: { viewModel.searchText = $0 }
                    ))
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
                        Text(currentFilterLabel(viewModel: viewModel))
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
                        minDate: timelineMinDate(viewModel: viewModel),
                        maxDate: timelineMaxDate(viewModel: viewModel),
                        currentDate: timelineMinDate(viewModel: viewModel),
                        onJump: { _ in },
                        onJumpFinal: { date in
                            Task {
                                await viewModel.scrollToDate(
                                    year: yearOf(date),
                                    month: monthOf(date),
                                    day: dayOf(date)
                                )
                            }
                        }
                    )
                    .frame(width: 60)
                }
            }
        }
    }

    // MARK: - Toolbar helpers(static,只给 messagesToolbar 内部用)

    private static func currentFilterLabel(viewModel: MessagesViewModel) -> String {
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

    private static func timelineMinDate(viewModel: MessagesViewModel) -> Date {
        // 取该月最早一天
        guard let first = viewModel.monthlyDayCount.last else { return Date() }
        var comp = DateComponents()
        comp.year = first.year; comp.month = first.month; comp.day = first.day
        return Calendar.current.date(from: comp) ?? Date()
    }

    private static func timelineMaxDate(viewModel: MessagesViewModel) -> Date {
        guard let first = viewModel.monthlyDayCount.first else { return Date() }
        var comp = DateComponents()
        comp.year = first.year; comp.month = first.month; comp.day = first.day
        comp.hour = 23; comp.minute = 59; comp.second = 59
        return Calendar.current.date(from: comp) ?? Date()
    }

    // MARK: - 媒体预览

    private func openPreview(message: Message, startIndex: Int) {
        let mediaList = message.mediaItems.map { $0.asMedia() }
        guard !mediaList.isEmpty else { return }
        let safe = max(0, min(startIndex, mediaList.count - 1))
        // 设置导航栏标题(MediaDetailView 的 .onAppear 还会再 updateWindowTitle 一次,
        // 但先在这里给个有意义的占位,避免 overlay 进入动画期间窗口标题闪一下)。
        if let text = message.text, !text.isEmpty {
            PreviewTitle.shared.title = String(text.prefix(30))
        } else {
            PreviewTitle.shared.title = "消息 #\(message.id)"
        }
        // 先释放消息流容器焦点,再插入预览 —— MediaDetailView 的 .onAppear 会异步
        // 把自己置为 firstResponder,届时键盘事件由它接管。
        feedFocused = false
        previewIndex = safe
        previewState = PreviewState(
            id: UUID(),
            mediaList: mediaList
        )
    }

    private func closePreview() {
        previewState = nil
        // async 一拍 —— @FocusState 在 view 拆除过程中同步设置偶发被吞,
        // 等 overlay 完全 dismiss 后再恢复焦点是 SwiftUI 社区验证过的稳妥写法。
        // 焦点收回消息流容器后,下一次按空格不会被旁边的 focusable 元素截胡。
        DispatchQueue.main.async {
            feedFocused = true
        }
    }
}

// MARK: - 文件级日期组件提取(static toolbar 工厂内使用)
//
// 原来是 MessagesView 的实例方法;现在 toolbar 拆成 static func,这些 helper
// 无 self 可用,改成 file-private 自由函数,语义不变。

private func yearOf(_ d: Date) -> Int { Calendar.current.component(.year, from: d) }
private func monthOf(_ d: Date) -> Int { Calendar.current.component(.month, from: d) }
private func dayOf(_ d: Date) -> Int { Calendar.current.component(.day, from: d) }

// MARK: - 预览状态

/// 媒体预览的单一状态载体。每次打开都创建新实例(新 UUID),配合
/// `.id(state.id)` 强制 MediaDetailView 重建,避免上一次 session 的
/// AVPlayer / @FocusState / chromeVisible 等内部状态串到新一次。
///
/// 当前索引另存在 MessagesView 的 `@State previewIndex`,不挂在这里 ——
/// 否则翻页改写引用包装的 .value 时 SwiftUI 无法追踪到 PreviewState 的依赖,
/// 父 view 不会重算 body,导致从第二次起翻页失效(只在第一对相邻项间来回)。
private struct PreviewState {
    let id: UUID
    let mediaList: [Media]
}
