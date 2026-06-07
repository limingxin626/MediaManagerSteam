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
//       基于 ViewModel.loadedFlatItems 提供 globalIndex。
//

import SwiftUI

struct MediaLibraryView: View {
    @StateObject private var viewModel = MediaLibraryViewModel()

    // 详情 sheet
    @State private var detailIndex: Int = 0
    @State private var showDetail: Bool = false

    // 选中态 - 与详情解耦,单击只改它
    @State private var selectedIndex: Int? = nil
    @FocusState private var gridFocused: Bool

    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                header

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

                Spacer(minLength: 0)
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
        .sheet(isPresented: $showDetail) {
            MediaDetailView(
                mediaList: viewModel.loadedFlatItems,
                currentIndex: $detailIndex,
                hasMore: false,
                onNeedMore: { /* 桶按需加载,详情翻页时如果到末尾再考虑 */ }
            )
        }
        .onAppear {
            Task { await viewModel.loadInitial() }
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
        .onChange(of: showDetail) { _, isShown in
            if !isShown { selectedIndex = detailIndex }
        }
        .refreshable {
            await viewModel.refresh()
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: 12) {
            HStack {
                Text("媒体库")
                    .font(.largeTitle)
                    .fontWeight(.bold)

                Spacer()

                Button(action: { Task { await viewModel.toggleStarredOnly() } }) {
                    Image(systemName: viewModel.showOnlyStarred ? "star.fill" : "star")
                        .font(.system(size: 16))
                        .foregroundColor(viewModel.showOnlyStarred ? .orange : .gray)
                }
            }

            HStack(spacing: 8) {
                ForEach(["全部", "图片", "视频"], id: \.self) { type in
                    Button(action: {
                        Task {
                            let typeValue: String? = type == "全部" ? nil : (type == "图片" ? "image" : "video")
                            await viewModel.changeMediaType(typeValue)
                        }
                    }) {
                        Text(type)
                            .font(.caption)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(
                                (type == "全部" && viewModel.selectedMediaType == nil) ||
                                (type == "图片" && viewModel.selectedMediaType == "image") ||
                                (type == "视频" && viewModel.selectedMediaType == "video")
                                ? Color.blue : Color.gray.opacity(0.2)
                            )
                            .foregroundColor(
                                (type == "全部" && viewModel.selectedMediaType == nil) ||
                                (type == "图片" && viewModel.selectedMediaType == "image") ||
                                (type == "视频" && viewModel.selectedMediaType == "video")
                                ? .white : .secondary
                            )
                            .cornerRadius(4)
                    }
                }
                Spacer()
            }
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
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
            let globalIndex = mediaIndexInLoaded(mediaId: item.id) ?? 0
            MediaGridItem(media: item, isSelected: selectedIndex == globalIndex)
                .onTapGesture(count: 2) {
                    selectedIndex = globalIndex
                    detailIndex = globalIndex
                    showDetail = true
                }
                .onTapGesture(count: 1) {
                    selectedIndex = globalIndex
                }
        } else {
            // 占位:item 还没加载到此 idx,撑住格子位置不坍缩
            Rectangle()
                .fill(Color.gray.opacity(0.12))
                .cornerRadius(4)
        }
    }

    private func mediaIndexInLoaded(mediaId: Int) -> Int? {
        viewModel.loadedFlatItems.firstIndex { $0.id == mediaId }
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
            if showDetail { return .ignored }
            let target = selectedIndex ?? 0
            selectedIndex = target
            detailIndex = target
            showDetail = true
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
    MediaLibraryView()
}
