//
//  MediaLibraryView.swift
//  MyNote
//
//  媒体库视图 - 网格展示所有媒体(本地 SQLite 数据源)。
//  交互模型贴近 Finder / macOS 照片:
//    - 单击 -> 仅选中,不打开预览
//    - 双击 -> 打开预览
//    - 方向键 -> 在网格内移动选中(↑/↓ 按列对齐,边界处停住不 wrap)
//    - 空格  -> 切换预览的打开/关闭
//  时间轴:右侧 DateScrubber 固定显示,拖动可跳转到任意日期桶.
//

import SwiftUI

struct MediaLibraryView: View {
    @StateObject private var viewModel = MediaLibraryViewModel()
    // 用 index 而非 Media,这样左右切换只改 index,sheet 不重建。
    @State private var detailIndex: Int = 0
    @State private var showDetail: Bool = false
    // 选中态 - 与预览态解耦,单击只动这个。
    @State private var selectedIndex: Int? = nil
    // 网格的键盘焦点 - .focusable + .focused + .onKeyPress 三件套需要它。
    @FocusState private var gridFocused: Bool

    // 列数提成常量,方向键的几何换算和 columns 都要用。
    private let columnCount = 4

    private var columns: [GridItem] {
        Array(repeating: GridItem(.flexible(), spacing: 8), count: columnCount)
    }

    // Scrubber 用
    private var timelineMinDate: Date {
        viewModel.timeline.last?.date ?? Date()
    }
    private var timelineMaxDate: Date {
        viewModel.timeline.first?.date ?? Date()
    }

    var body: some View {
        ZStack {
            VStack(spacing: 0) {
                header

                if viewModel.isLoading {
                    VStack {
                        Spacer()
                        ProgressView()
                        Spacer()
                    }
                } else if viewModel.media.isEmpty {
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
                    grid
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
                mediaList: viewModel.media,
                currentIndex: $detailIndex,
                hasMore: viewModel.hasMore,
                onNeedMore: { await viewModel.loadMore() }
            )
        }
        .onAppear {
            Task {
                await viewModel.loadTimeline()
                await viewModel.loadInitial()
            }
            // 进入页面就让网格拿到焦点,方向键/空格立刻可用。
            gridFocused = true
        }
        // 首屏(或过滤切换)拉完数据后,默认选中第 0 项。
        // 监听 count 而非整个 [Media] - Media 没有 Equatable,且 count 已经能覆盖
        // 三种触发场景:loadInitial(0→N)、loadMore(N→N+k)、filter 切换(N→M)。
        .onChange(of: viewModel.media.count) { _, newCount in
            if newCount == 0 {
                selectedIndex = nil
            } else if selectedIndex == nil {
                selectedIndex = 0
            } else if let i = selectedIndex, i >= newCount {
                // 过滤切换后老索引越界,夹回末项。
                selectedIndex = newCount - 1
            }
        }
        // 过滤变化时主动把选中重置 - data 还没回来就先清掉,
        // 等 viewModel.media 变化的 onChange 再设回 0。
        .onChange(of: viewModel.selectedMediaType) { _, _ in selectedIndex = nil }
        .onChange(of: viewModel.showOnlyStarred) { _, _ in selectedIndex = nil }
        // 预览关闭后,把网格选中对到预览里最后看的那张。
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

    // MARK: - Grid

    private var grid: some View {
        HStack(spacing: 0) {
            // 主内容区
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVGrid(columns: columns, spacing: 8) {
                        ForEach(viewModel.buckets) { bucket in
                            // 日期标题行
                            bucketHeaderView(bucket)
                                .id("header-\(bucket.id)")

                            // 该天的媒体网格
                            ForEach(bucket.items) { mediaItem in
                                mediaItemView(mediaItem)
                            }
                        }

                        // 加载更多
                        if viewModel.hasMore {
                            VStack {
                                if viewModel.isLoadingMore {
                                    ProgressView()
                                } else {
                                    Text("加载更多")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                            .frame(height: 80)
                            .gridCellUnsizedAxes(.horizontal)
                            .onAppear {
                                Task { await viewModel.loadMore() }
                            }
                        }
                    }
                    .padding(8)
                }
                // 键盘焦点 + 方向键/空格响应。
                .focusable(true)
                .focused($gridFocused)
                .onKeyPress { press in
                    handleKeyPress(press)
                }
                // Scrubber 跳转:滚动到目标桶
                .onChange(of: viewModel._scrollToBucketIndex) { _, newIdx in
                    guard let idx = newIdx, viewModel.buckets.indices.contains(idx) else { return }
                    withAnimation(.easeOut(duration: 0.3)) {
                        proxy.scrollTo("header-\(viewModel.buckets[idx].id)", anchor: .top)
                    }
                }
            }

            // 右侧时间轴 Scrubber
            if !viewModel.timeline.isEmpty {
                DateScrubber(
                    timeline: viewModel.timeline,
                    minDate: timelineMinDate,
                    maxDate: timelineMaxDate,
                    currentDate: $viewModel.currentDate,
                    onJump: { date in
                        viewModel.scrollToDate(date)
                    },
                    onJumpFinal: { date in
                        viewModel.scrollToDate(date)
                    }
                )
                .frame(width: 62)
                .padding(.trailing, 4)
            }
        }
    }

    /// 单个媒体项视图(拆分出来避免编译器类型爆炸)。
    @ViewBuilder
    private func mediaItemView(_ mediaItem: Media) -> some View {
        let globalIndex = mediaIndexInAll(mediaId: mediaItem.id) ?? 0
        MediaGridItem(media: mediaItem, isSelected: selectedIndex == globalIndex)
            .id(mediaItem.id)
            .onTapGesture(count: 2) {
                selectedIndex = globalIndex
                detailIndex = globalIndex
                showDetail = true
            }
            .onTapGesture(count: 1) {
                selectedIndex = globalIndex
            }
    }

    /// 日期标题行。
    private func bucketHeaderView(_ bucket: MediaDateBucket) -> some View {
        HStack {
            Text(bucket.headerText)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.secondary)
            Spacer()
        }
        .padding(.vertical, 6)
        .padding(.horizontal, 4)
        .background(Color(NSColor.controlBackgroundColor).opacity(0.5))
    }

    /// 在 viewModel.media 中查找指定 mediaId 的全局索引。
    private func mediaIndexInAll(mediaId: Int) -> Int? {
        viewModel.media.firstIndex { $0.id == mediaId }
    }

    // MARK: - Keyboard

    /// 网格层处理方向键 + 空格。返回 .handled 表示事件已消费,.ignored 让它继续冒泡。
    private func handleKeyPress(_ press: KeyPress) -> KeyPress.Result {
        let count = viewModel.media.count
        guard count > 0 else { return .ignored }

        switch press.key {
        case .leftArrow:
            moveSelection { ($0 ?? 1) - 1 }
            return .handled
        case .rightArrow:
            moveSelection { ($0 ?? -1) + 1 }
            return .handled
        case .upArrow:
            moveSelection { ($0 ?? columnCount) - columnCount }
            return .handled
        case .downArrow:
            moveSelection { ($0 ?? -columnCount) + columnCount }
            return .handled
        case .space:
            // 预览已开,让事件冒泡给 sheet 自己处理关闭。
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

    /// 用 transform 计算新索引,并夹到 [0, count-1]。selectedIndex == nil 时由
    /// transform 内的 ?? 兜底,效果是任一方向键都把选中拽到 0(再加方向偏移再夹回)。
    private func moveSelection(_ transform: (Int?) -> Int) {
        let count = viewModel.media.count
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
            // 选中描边:用 accent color 贴系统外观,3pt 线宽够显眼又不挡内容。
            // 放在 ZStack 顶部的 overlay 里,不会推动 layout。
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    .stroke(Color.accentColor, lineWidth: 3)
                    .opacity(isSelected ? 1 : 0)
            )

            // 第一期只读:星标仅显示状态,不可点击
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
