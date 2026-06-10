//
//  MediaLibraryView.swift
//  MyNote
//
//  媒体库视图 - 基于 timeline 派生的虚拟化网格 + 右侧 DateScrubber 日期导航。
//
//  架构与 vue/src/views/Media.vue + useVirtualGrid.ts 同构:
//    1. 网格用 ScrollView + ZStack 绝对定位渲染可视范围内的 cell,
//       内容总高由 timeline 全量算出,跳转到任意桶不依赖该桶已被实例化。
//    2. NSScrollViewBridge 把 SwiftUI ScrollView 桥到 AppKit,
//       支持「程序化跳转任意 y」+「实时回写 scrollTop」。
//    3. 单击/双击/方向键/空格交互复用旧的 Finder 风格选中逻辑,
//       globalIndex 由 ViewModel.visibleCells 算前缀和直接给到 cell,
//       cell 层不再做线性查找;单击 / 双击判别用 CellTapModifier
//       自定义(避免 SwiftUI 等系统双击间隔造成的 1s 延迟)。
//

import SwiftUI

struct MediaLibraryView: View {
    @ObservedObject var viewModel: MediaLibraryViewModel

    // NavigationStack path — 推入 MediaPreviewDestination 即打开预览,pop 即关闭。
    @State private var navigationPath = NavigationPath()

    // 选中态 - 与详情解耦,单击只改它
    @State private var selectedIndex: Int? = nil
    @FocusState private var gridFocused: Bool

    var body: some View {
        NavigationStack(path: $navigationPath) {
            ZStack {
                // 底层:网格 + 错误提示
                ZStack {
                    Group {
                        if viewModel.isLoading && viewModel.buckets.isEmpty {
                            VStack {
                                Spacer()
                                ProgressView()
                                Spacer()
                            }
                        } else if viewModel.buckets.isEmpty {
                            VStack {
                                Spacer()
                                Image(systemName: "photo.on.rectangle")
                                    .font(.system(size: 48))
                                    .foregroundColor(.gray)
                                Text("暂无媒体")
                                    .foregroundColor(.secondary)
                                Spacer()
                            }
                        } else {
                            gridWithScrubber
                        }
                    }

                    if let error = viewModel.errorMessage {
                        VStack {
                            HStack {
                                Text(error)
                                    .font(.caption)
                                    .foregroundColor(.red)
                                Spacer()
                                Button(action: { viewModel.errorMessage = nil }) {
                                    Image(systemName: "xmark")
                                }
                            }
                            .padding()
                            .background(Color.red.opacity(0.1))
                            .cornerRadius(8)
                            .padding()

                            Spacer()
                        }
                    }
                }
            }
            .navigationTitle(PreviewTitle.shared.title.isEmpty ? "媒体库" : PreviewTitle.shared.title)
            .navigationDestination(for: MediaPreviewDestination.self) { destination in
                MediaDetailView(
                    mediaList: destination.mediaList,
                    currentIndex: destination.currentIndexBinding ?? .constant(destination.startIndex),
                    hasMore: false,
                    onNeedMore: { /* 桶按需加载暂未启用 */ },
                    onClose: { closePreview() }
                )
            }
        }
        .onAppear {
            Task { await viewModel.loadInitialIfNeeded() }
            gridFocused = true
        }
        // 首屏 / 过滤切换后默认选中第 0 项
        .onChange(of: viewModel.loadedFlatItems.count) { _, newCount in
            if newCount == 0 {
                selectedIndex = nil
            } else if selectedIndex == nil {
                selectedIndex = 0
            } else if let i = selectedIndex, i >= newCount {
                selectedIndex = newCount - 1
            }
        }
        .onChange(of: viewModel.selectedMediaType) { _, _ in selectedIndex = nil }
        .onChange(of: viewModel.showOnlyStarred) { _, _ in selectedIndex = nil }
        // 选中项变化时(方向键 / 详情关闭同步)自动滚到可视范围
        .onChange(of: selectedIndex) { _, newValue in
            guard let i = newValue, i < viewModel.loadedFlatItems.count else { return }
            viewModel.ensureMediaVisible(mediaId: viewModel.loadedFlatItems[i].id)
        }
        .refreshable {
            await viewModel.refresh()
        }
    }

    // MARK: - 顶栏(toolbar)
    //
    // toolbar 已上提到 ContentView,这里只提供工厂方法供其调用。改成 static
    // 同 MessagesView.messagesToolbar —— ZStack 同时持多个 page 时,各自 page 内
    // 挂 .toolbar 会被 AppKit 合并到窗口顶栏导致重叠(opacity=0 不影响 toolbar 合并)。
    // 上提后 ContentView switch selectedTab 单一来源,每个 tab 一套 toolbar 互不打架。

    @ToolbarContentBuilder
    static func mediaToolbar(viewModel: MediaLibraryViewModel) -> some ToolbarContent {
        ToolbarItem(placement: .principal) {
            Picker("媒体类型", selection: mediaTypeBinding(viewModel: viewModel)) {
                Text("全部").tag(MediaTypeFilter.all)
                Text("图片").tag(MediaTypeFilter.image)
                Text("视频").tag(MediaTypeFilter.video)
            }
            .pickerStyle(.segmented)
            .labelsHidden()
        }
        ToolbarItem(placement: .primaryAction) {
            Button { Task { await viewModel.toggleStarredOnly() } } label: {
                Image(systemName: viewModel.showOnlyStarred ? "star.fill" : "star")
            }
            .help(viewModel.showOnlyStarred ? "显示全部" : "仅显示星标")
        }
    }

    /// 把 viewModel.selectedMediaType (String?) 桥到 Picker 的 MediaTypeFilter 枚举
    /// selection 上。setter 同步调 changeMediaType 触发 reload,与原 chip 行为一致。
    /// 改成 static 是为了 mediaToolbar 在 ContentView 调用上下文里无 self 可用。
    private static func mediaTypeBinding(viewModel: MediaLibraryViewModel) -> Binding<MediaTypeFilter> {
        Binding(
            get: { MediaTypeFilter(rawValue: viewModel.selectedMediaType ?? "") ?? .all },
            set: { newValue in
                let mapped: String? = newValue == .all ? nil : newValue.rawValue
                Task { await viewModel.changeMediaType(mapped) }
            }
        )
    }

    // MARK: - Grid + Scrubber 整体

    private var gridWithScrubber: some View {
        HStack(spacing: 0) {
            grid
                .frame(maxWidth: .infinity)

            if !viewModel.timeline.isEmpty {
                DateScrubber(
                    timeline: viewModel.timeline,
                    minDate: timelineMinDate,
                    maxDate: timelineMaxDate,
                    currentDate: viewModel.currentDate,
                    onJump: { date in
                        viewModel.setDispatchPaused(true)
                        viewModel.scrollToDate(date)
                    },
                    onJumpFinal: { date in
                        viewModel.scrollToDate(date)
                        viewModel.setDispatchPaused(false)
                    }
                )
                .frame(width: 62)
                .padding(.trailing, 4)
            }
        }
    }

    private var timelineMinDate: Date {
        // timeline 按 DESC,last 是最早 → 取其 0 点
        guard let last = viewModel.timeline.last else { return Date() }
        var comp = DateComponents()
        comp.year = last.year; comp.month = last.month; comp.day = last.day
        return Calendar.current.date(from: comp) ?? Date()
    }

    private var timelineMaxDate: Date {
        // first 是最新 → 取其 23:59:59,避免最新一天被压在 0% 顶端
        guard let first = viewModel.timeline.first else { return Date() }
        var comp = DateComponents()
        comp.year = first.year; comp.month = first.month; comp.day = first.day
        comp.hour = 23; comp.minute = 59; comp.second = 59
        return Calendar.current.date(from: comp) ?? Date()
    }

    // MARK: - Grid 主体

    private var grid: some View {
        VirtualScrollView(
            contentHeight: viewModel.totalContentHeight,
            scrollTop: Binding(
                get: { viewModel.scrollTop },
                set: { viewModel.setScrollTop($0) }
            ),
            viewportHeight: Binding(
                get: { viewModel.viewportHeight },
                set: { viewModel.setViewportHeight($0) }
            ),
            containerWidth: Binding(
                get: { viewModel.containerWidth },
                set: { viewModel.setContainerWidth($0) }
            ),
            jumpTrigger: viewModel.jumpTrigger,
            targetY: viewModel.jumpTargetY
        ) {
            ZStack(alignment: .topLeading) {
                // 桶头(只渲染可视范围 + PREFETCH 内的)
                ForEach(viewModel.visibleBuckets) { b in
                    bucketHeaderView(b)
                        .frame(width: viewModel.containerWidth, height: 28, alignment: .leading)
                        .offset(x: 0, y: b.headerOffset)
                }

                // 可见 cell(更窄的 RENDER_OVERSCAN)
                ForEach(viewModel.visibleCells) { cell in
                    cellView(cell)
                        .frame(width: cell.size, height: cell.size)
                        .offset(x: cell.x, y: cell.y)
                }
            }
            .frame(
                width: max(viewModel.containerWidth, 1),
                height: max(viewModel.totalContentHeight, 1),
                alignment: .topLeading
            )
        }
        .focusable(true)
        .focused($gridFocused)
        .focusEffectDisabled(true)  // 关掉系统默认的蓝色 NSFocusRing,选中态已有自己的 Color.accentColor 描边
        .onKeyPress { handleKeyPress($0) }
    }

    // MARK: - 桶头 / cell

    private func bucketHeaderView(_ b: BucketLayout) -> some View {
        HStack {
            Text(b.headerText)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.secondary)
            Spacer()
        }
        .padding(.vertical, 6)
        .padding(.horizontal, 4)
    }

    @ViewBuilder
    private func cellView(_ cell: VisibleCell) -> some View {
        if let item = cell.item {
            // globalIndex 已由 ViewModel 在 visibleCells 里算好,直接读,
            // 避免对 loadedFlatItems 做线性扫(每个 cell 每次 render 都跑)。
            let globalIndex = cell.globalIndex
            MediaGridItem(media: item, isSelected: selectedIndex == globalIndex)
                .cellTap(
                    globalIndex: globalIndex,
                    onSingle: { _ in selectedIndex = globalIndex },
                    onDouble: { _ in
                        selectedIndex = globalIndex
                        openPreview(at: globalIndex)
                    }
                )
        } else {
            // 占位:item 还没加载到此 idx,撑住格子位置不坍缩
            Rectangle()
                .fill(Color.gray.opacity(0.12))
                .cornerRadius(4)
        }
    }

    // MARK: - Keyboard

    private func handleKeyPress(_ press: KeyPress) -> KeyPress.Result {
        let count = viewModel.loadedFlatItems.count
        guard count > 0 else { return .ignored }

        switch press.key {
        case .leftArrow:
            moveSelection { ($0 ?? 1) - 1 }
            return .handled
        case .rightArrow:
            moveSelection { ($0 ?? -1) + 1 }
            return .handled
        case .upArrow:
            moveSelection { ($0 ?? viewModel.cols) - viewModel.cols }
            return .handled
        case .downArrow:
            moveSelection { ($0 ?? -viewModel.cols) + viewModel.cols }
            return .handled
        case .space:
            let target = selectedIndex ?? 0
            selectedIndex = target
            openPreview(at: target)
            return .handled
        default:
            return .ignored
        }
    }

    private func moveSelection(_ transform: (Int?) -> Int) {
        let count = viewModel.loadedFlatItems.count
        guard count > 0 else { return }
        let raw = transform(selectedIndex)
        selectedIndex = max(0, min(raw, count - 1))
    }

    /// 双击 / 空格触发预览的统一入口 — 推入 NavigationDestination,窗口标题自动切换。
    private func openPreview(at index: Int) {
        let items = viewModel.loadedFlatItems
        guard !items.isEmpty else { return }
        let safeIndex = max(0, min(index, items.count - 1))
        // 用一个独立的 Box 包裹可变的 Int 引用,避免 @State 跨多次打开时的旧值串扰。
        let box = IndexBox(value: safeIndex)
        let binding = Binding(get: { box.value }, set: { box.value = $0 })
        let destination = MediaPreviewDestination(
            mediaList: items,
            startIndex: safeIndex,
            currentIndexBinding: binding
        )
        previewBox = box
        navigationPath.append(destination)
        gridFocused = false
    }

    /// MediaDetailView 的关闭回调(ESC / 空格 / ×)。pop 回媒体库,同步选中态,
    /// 恢复网格焦点。后续 onChange(of: selectedIndex) 会自动调 ensureMediaVisible。
    private func closePreview() {
        if let box = previewBox {
            selectedIndex = box.value
        }
        previewBox = nil
        navigationPath.removeLast()
        gridFocused = true
    }

    /// 用 @State 持有最近一次打开的 IndexBox — 关闭时据其同步 selectedIndex。
    /// 每次 openPreview 重新创建,确保上一次的值不残留。
    @State private var previewBox: IndexBox? = nil
}

// MARK: - Grid Item

struct MediaGridItem: View {
    let media: Media
    var isSelected: Bool = false

    var body: some View {
        ZStack(alignment: .topTrailing) {
            ZStack {
                LocalThumbView(media: media)

                if let mime = media.mimeType, mime.hasPrefix("video/") {
                    Image(systemName: "play.circle.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.white)
                        .shadow(radius: 2)
                }
            }
            .aspectRatio(1, contentMode: .fit)
            .clipped()
            .cornerRadius(4)
            .contentShape(Rectangle())
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    .stroke(Color.accentColor, lineWidth: 3)
                    .opacity(isSelected ? 1 : 0)
            )

            if media.starred {
                Image(systemName: "star.fill")
                    .font(.system(size: 12))
                    .foregroundColor(.orange)
                    .padding(6)
                    .background(Color.black.opacity(0.3))
                    .clipShape(Circle())
                    .padding(6)
            }
        }
    }
}

#Preview {
    NavigationStack {
        MediaLibraryView(viewModel: MediaLibraryViewModel())
    }
}

// MARK: - 单 / 双击判别

/// 在 macOS 上,如果同一个 view 上同时挂 `.onTapGesture(count: 1)` 和
/// `.onTapGesture(count: 2)`,SwiftUI 必须等满系统的双击间隔
/// (`NSEvent.doubleClickInterval()`,默认 500ms)才能确定是单击还是双击,
/// 单击高亮因此会拖到接近 1 秒 —— 这就是「点击媒体卡顿」的根因。
///
/// 这里只挂 `.onTapGesture(count: 1)`,内部用时间戳 + Task 自己判别:
///   - 第一次 tap 记时间戳,起一个 250ms 的延迟任务准备触发「单击」;
///   - 250ms 内再来一次 tap → 取消延迟任务,改派发「双击」;
///   - 250ms 内没有第二次 → 延迟任务自然唤醒,派发「单击」。
///
/// 250ms 略小于系统默认 500ms,既能让单击反馈接近即时,又足够覆盖
/// 多数人的真实双击节奏。
private struct CellTapModifier: ViewModifier {
    let globalIndex: Int
    let onSingle: (Int) -> Void
    let onDouble: (Int) -> Void

    /// 250ms 在绝大多数用户的双击节奏之内;系统双击间隔调长的人会偶尔
    /// 把「想双击」误判为两次单击,这种情况可让他们改系统设置。
    private static let doubleTapWindow: TimeInterval = 0.25

    @State private var lastTapTime: Date?
    @State private var pendingSingleTask: Task<Void, Never>?

    func body(content: Content) -> some View {
        content.onTapGesture {
            handleTap()
        }
    }

    private func handleTap() {
        let now = Date()
        if let last = lastTapTime, now.timeIntervalSince(last) < Self.doubleTapWindow {
            // 第二次 tap 落在窗口内:取消挂起的单击,立刻派发双击。
            pendingSingleTask?.cancel()
            pendingSingleTask = nil
            lastTapTime = nil
            onDouble(globalIndex)
        } else {
            // 第一次 tap(或离上次太远):记时间戳并排一个延迟的单击。
            // 用 capturedIndex 闭包捕获,避免 task 醒来时 globalIndex 已被新值替换。
            let capturedIndex = globalIndex
            lastTapTime = now
            pendingSingleTask = Task { @MainActor [onSingle] in
                try? await Task.sleep(nanoseconds: UInt64(Self.doubleTapWindow * 1_000_000_000))
                guard !Task.isCancelled else { return }
                onSingle(capturedIndex)
            }
        }
    }
}

private extension View {
    /// 网格 cell 的单击 / 双击判别入口。挂这个等价于
    /// `.onTapGesture(count: 1)`,但内部用时间戳自行判别双击,
    /// 避免 SwiftUI 等待系统双击间隔造成的 1 秒延迟。
    func cellTap(
        globalIndex: Int,
        onSingle: @escaping (Int) -> Void,
        onDouble: @escaping (Int) -> Void
    ) -> some View {
        modifier(CellTapModifier(
            globalIndex: globalIndex,
            onSingle: onSingle,
            onDouble: onDouble
        ))
    }
}
