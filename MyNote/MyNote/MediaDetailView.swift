//
//  MediaDetailView.swift
//  MyNote
//
//  媒体详情视图 - 图片大图 / 视频内嵌播放。读本地文件,不走 HTTP。
//  支持左右键 / 按钮在列表内切换上一张/下一张,切到末尾时触发 loadMore。
//

import SwiftUI
import AppKit
import AVKit

struct MediaDetailView: View {
    /// 当前要展示的列表(通常是 ViewModel.media 的快照引用)。
    let mediaList: [Media]
    /// 当前索引。绑定回外层,关闭时外层可知道最后看到哪一张。
    @Binding var currentIndex: Int
    /// 是否还能继续翻到更后面 —— 用来决定要不要触发 loadMore。
    let hasMore: Bool
    /// 走到列表末尾、还能加载更多时回调外层异步拉下一页。
    let onNeedMore: () async -> Void
    /// 关闭预览的统一回调 —— 外层(MediaLibraryView)负责清状态 / 同步选中态 / 切焦点。
    let onClose: () -> Void

    /// 视频播放器随当前 media 重建,切换时旧 player 自动释放。
    @State private var player: AVPlayer? = nil

    /// header / metadata 自动淡入淡出 —— 鼠标静止 ~1.5s 后置 false。
    @State private var chromeVisible: Bool = true
    /// 焦点 — 让 .onKeyPress 在打开预览时立即接管键盘,不再受 NavigationSplitView 焦点抢占影响。
    @FocusState private var isFocused: Bool
    /// 最近一次「活动事件」起的隐藏倒计时;新事件来了 cancel 旧的、起新的。
    @State private var hideTask: Task<Void, Never>? = nil
    /// AppKit 鼠标移动监视器 —— 全屏时 .onHover 永远是 true,只能走 NSEvent。
    @State private var mouseMonitor: Any? = nil
    /// AppKit 键盘监视器 —— SwiftUI .onKeyPress 在 overlay 模式下焦点链不稳:
    /// 切换媒体重建 content 子树时 @FocusState 偶发被吞,后续左右键收不到 →
    /// "翻不动";另一些时候同一次按键既被 .onKeyPress 又被系统其它响应者
    /// 处理 → "会跳"(连跳两项)。改走 local monitor 在 SwiftUI 之前抢
    /// 拦截,返回 nil 吞掉事件,行为稳定不受焦点影响。
    @State private var keyMonitor: Any? = nil

    private var current: Media? {
        guard mediaList.indices.contains(currentIndex) else { return nil }
        return mediaList[currentIndex]
    }

    private var canGoPrev: Bool { currentIndex > 0 }
    private var canGoNext: Bool {
        currentIndex < mediaList.count - 1 || hasMore
    }

    var body: some View {
        VStack(spacing: 0) {
            // 媒体本体 + 左右翻页热区。背景随系统主题走:
            //   浅色 → 接近白,深色 → 接近黑 —— 与 Photos.app 等系统 app 的「舞台」色一致。
            ZStack {
                Color(.windowBackgroundColor)
                content
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                HStack(spacing: 0) {
                    pageButton(systemName: "chevron.left", enabled: canGoPrev, action: goPrev)
                    Spacer(minLength: 0)
                    pageButton(systemName: "chevron.right", enabled: canGoNext, action: goNext)
                }
                .padding(.horizontal, 12)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            metadata
                .padding()
                .opacity(chromeVisible ? 1 : 0)
                .animation(.easeInOut(duration: 0.25), value: chromeVisible)
        }
        // 尺寸由外层 Window scene 控制(全屏时即整个屏幕),不再在 view 内部强约束。
        .onAppear {
            rebuildPlayer()
            startMouseTracking()
            startKeyTracking()
            scheduleHide()
            updateWindowTitle()
            // 把焦点转移到本 view,使 .onKeyPress 生效
            DispatchQueue.main.async { _ = isFocused = true }
        }
        .focusable(true)
        .focused($isFocused)
        // 键盘处理统一走 AppKit local monitor(startKeyTracking),不挂 .onKeyPress —
        // SwiftUI 焦点链在 overlay 模式下不稳,monitor 抢在事件分发前拦截更可靠。
        .focusEffectDisabled(true)
        .onChange(of: currentIndex) { _, _ in
            rebuildPlayer()
            bumpActivity()
            updateWindowTitle()
        }
        .onDisappear {
            player?.pause()
            player = nil
            stopMouseTracking()
            stopKeyTracking()
            hideTask?.cancel()
            PreviewTitle.shared.title = ""
            for window in NSApp.windows {
                window.title = ""
            }
        }
    }

    // MARK: - Content

    @ViewBuilder
    private var content: some View {
        if let media = current {
            if let url = media.localFileURL, media.isRepoAvailable {
                if let mime = media.mimeType, mime.hasPrefix("video/") {
                    if let player {
                        VideoPlayer(player: player)
                    } else {
                        placeholder("视频加载中…")
                    }
                } else if let mime = media.mimeType, mime.hasPrefix("image/") {
                    // 详情页读**原图** —— GIF / animated webp 走 AnimatedImageView
                    // 播原图(CGImageSource 解码,慢但保证全分辨率全帧)。
                    // 不走 MP4 preview:MP4 只给 grid 缩略图用,详情要看原图全貌。
                    switch AnimatedImageFormatDetector.detect(url: url) {
                    case .animated:
                        AnimatedImageView(url: url, contentMode: .fit)
                    case .staticImage, .unsupported:
                        LocalLargeImageView(media: media, fileURL: url)
                    }
                } else {
                    placeholder("不支持的媒体类型: \(media.mimeType ?? "未知")")
                }
            } else if media.repoId != nil && !media.isRepoAvailable {
                placeholder("请插入 \(media.repoDisplayName) 硬盘")
            } else {
                placeholder("数据目录未配置")
            }
        } else {
            placeholder("无内容")
        }
    }

    private func placeholder(_ text: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 36))
                .foregroundColor(.gray)
            Text(text)
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
                .textSelection(.enabled)
        }
    }

    // MARK: - Page buttons

    private func pageButton(systemName: String, enabled: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: 22, weight: .semibold))
                .foregroundColor(.white)
                .frame(width: 44, height: 44)
                .background(Color.black.opacity(enabled ? 0.45 : 0.15))
                .clipShape(Circle())
        }
        .buttonStyle(.plain)
        .disabled(!enabled)
        .opacity(enabled ? 1 : 0.3)
    }

    // MARK: - Metadata

    private var metadata: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 第一行：文件属性标签
            HStack(spacing: 24) {
                if let media = current {
                    if let size = media.fileSize {
                        Label(formatFileSize(size), systemImage: "doc")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    if let w = media.width, let h = media.height {
                        Label("\(w) × \(h)", systemImage: "aspectratio")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    if let d = media.durationMs {
                        Label(formatDuration(d), systemImage: "clock")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                    if !media.tags.isEmpty {
                        ForEach(media.tags) { tag in
                            Text("#\(tag.name)")
                                .font(.caption)
                                .foregroundColor(.blue)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.blue.opacity(0.1))
                                .cornerRadius(4)
                        }
                    }
                } else {
                    Spacer()
                }
            }

            // 第二行：绝对路径
            if let media = current, let fileURL = media.localFileURL {
                HStack(spacing: 8) {
                    Image(systemName: "folder")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(fileURL.path)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .truncationMode(.middle)
                        .lineLimit(1)
                    Spacer()
                }
                .textSelection(.enabled)
            }
        }
        // 同样:覆盖在网格上,缺背景会让浅色 secondary 文字糊在 cell 缩略图上读不清。
        .background(Color(.windowBackgroundColor))
    }

    // MARK: - Keyboard / Title

    /// 把当前文件名写到 AppKit 窗口的 title bar 上(不是 SwiftUI navigation bar)。
    /// 媒体库的"媒体库"标题是 ContentView 用 .navigationTitle("媒体库") 渲染的,
    /// 在 NavigationSplitView detail 里会被提升到系统窗口标题栏;此处同步覆盖,
    /// 关闭预览时在 .onDisappear 里恢复空 title 让"媒体库"重新出现。
    private func updateWindowTitle() {
        let title: String
        if mediaList.indices.contains(currentIndex) {
            title = mediaList[currentIndex].filePath.components(separatedBy: "/").last ?? "媒体预览"
        } else {
            title = "媒体预览"
        }
        PreviewTitle.shared.title = title
        for window in NSApp.windows {
            window.title = title
        }
    }

    // MARK: - Navigation

    private func goPrev() {
        bumpActivity()
        guard canGoPrev else { return }
        currentIndex -= 1
    }

    private func goNext() {
        bumpActivity()
        guard canGoNext else { return }
        // 如果已经是最后一张但还有更多,先触发加载再前进。
        if currentIndex >= mediaList.count - 1 {
            if hasMore {
                Task {
                    await onNeedMore()
                    await MainActor.run {
                        if currentIndex < mediaList.count - 1 {
                            currentIndex += 1
                        }
                    }
                }
            }
            return
        }
        currentIndex += 1
    }

    /// 关闭预览的统一入口 —— 仅回调外层,本 view 不再持有任何跨 scene 状态。
    private func closePreview() {
        bumpActivity()
        onClose()
    }

    // MARK: - Chrome auto-hide

    /// 标记「有活动」—— 立即把 chrome 显示出来,并重启 1.5s 隐藏倒计时。
    private func bumpActivity() {
        chromeVisible = true
        scheduleHide()
    }

    /// 起一个 1.5s 后把 chrome 隐藏的 task。重复调用会 cancel 旧的、起新的。
    private func scheduleHide() {
        hideTask?.cancel()
        hideTask = Task { @MainActor in
            try? await Task.sleep(for: .seconds(1.5))
            if !Task.isCancelled {
                chromeVisible = false
            }
        }
    }

    /// 注册 AppKit 鼠标移动监视器 —— 全屏视图覆盖整屏,SwiftUI .onHover 永远 true,
    /// 抓不到「鼠标停下」的边沿,所以只能走 NSEvent。本地 monitor 仅限本进程。
    private func startMouseTracking() {
        guard mouseMonitor == nil else { return }
        mouseMonitor = NSEvent.addLocalMonitorForEvents(matching: .mouseMoved) { event in
            // 任何鼠标移动都算活动,即便位移 < 1pt —— Photos.app 也是这个行为。
            Task { @MainActor in
                bumpActivity()
            }
            return event
        }
    }

    private func stopMouseTracking() {
        if let monitor = mouseMonitor {
            NSEvent.removeMonitor(monitor)
            mouseMonitor = nil
        }
    }

    /// 注册键盘 local monitor —— 抢在 SwiftUI 焦点链之前处理翻页 / 关闭键,
    /// 返回 nil 吞掉事件防止 .onKeyPress 再次消费导致双触发("跳两项")。
    /// 仅响应单次 keyDown,不响应 keyRepeat —— 长按不会一秒翻 N 张,与
    /// Photos.app / 浏览器图片预览行为一致。
    private func startKeyTracking() {
        guard keyMonitor == nil else { return }
        keyMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
            // keyCode: 123=Left, 124=Right, 53=Escape, 49=Space
            switch event.keyCode {
            case 123:
                if !event.isARepeat { Task { @MainActor in goPrev() } }
                return nil
            case 124:
                if !event.isARepeat { Task { @MainActor in goNext() } }
                return nil
            case 53, 49:
                if !event.isARepeat { Task { @MainActor in closePreview() } }
                return nil
            default:
                return event
            }
        }
    }

    private func stopKeyTracking() {
        if let monitor = keyMonitor {
            NSEvent.removeMonitor(monitor)
            keyMonitor = nil
        }
    }

    // MARK: - Player lifecycle

    /// 切换 media 时重建 AVPlayer,旧 player 自动释放;非视频时清空。
    private func rebuildPlayer() {
        player?.pause()
        player = nil
        guard let media = current,
              let mime = media.mimeType, mime.hasPrefix("video/"),
              let url = media.localFileURL else { return }
        player = AVPlayer(url: url)
        player?.play()
    }

    // MARK: - Formatting

    private func formatFileSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }

    private func formatDuration(_ ms: Int) -> String {
        let s = ms / 1000
        let m = s / 60
        let h = m / 60
        if h > 0 {
            return String(format: "%d:%02d:%02d", h, m % 60, s % 60)
        }
        return String(format: "%d:%02d", m, s % 60)
    }
}

// MARK: - 大图加载

/// 大图视图:先用网格已经缓存的缩略图秒级占位,大图在后台解码完成后无缝替换。
/// 这样从网格点开看到的"第一帧"立刻就是这张图(模糊版),不会闪黑底。
private struct LocalLargeImageView: View {
    let media: Media
    let fileURL: URL

    /// nil 表示还没拿到任何图(连缩略图都没缓存),显示进度条。
    @State private var image: NSImage? = nil
    /// 当前 image 是不是缩略图占位 —— true 时大图还在后台解,但 UI 已经有东西看了。
    @State private var isPlaceholder: Bool = false
    @State private var failed = false
    @State private var errorDetails: String = ""

    var body: some View {
        ZStack {
            if let image {
                // .interpolation(.medium) 让缩略图被拉大时不至于太糊
                Image(nsImage: image)
                    .resizable()
                    .interpolation(.medium)
                    .scaledToFit()
            } else if failed {
                VStack(spacing: 12) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 36))
                        .foregroundColor(.gray)
                    Text("无法加载图片")
                        .foregroundColor(.gray)
                    VStack(alignment: .leading, spacing: 8) {
                        Text("路径: \(fileURL.path)")
                            .font(.caption2)
                            .foregroundColor(.gray)
                            .textSelection(.enabled)
                        if !errorDetails.isEmpty {
                            Text(errorDetails)
                                .font(.caption2)
                                .foregroundColor(.orange)
                                .textSelection(.enabled)
                        }
                    }
                    .padding(8)
                    .background(Color.gray.opacity(0.1))
                    .cornerRadius(4)
                }
            } else {
                ProgressView()
            }
        }
        .task(id: media.id) {
            failed = false
            errorDetails = ""

            // Step 1: 先同步命中网格缩略图缓存,立刻有画面。
            // LocalImageLoader 是 actor,await 是必要的,但缓存命中只是字典查询,基本零延迟。
            if let thumb = await LocalImageLoader.shared.cached(mediaId: media.id) {
                image = thumb
                isPlaceholder = true
            } else {
                // 网格没显示过这张(直接打开第一张就可能),清空让 ProgressView 顶上。
                image = nil
                isPlaceholder = false
            }

            // Step 2: 后台解大图,完成后替换。
            let url = fileURL
            let loaded: NSImage? = await Task.detached(priority: .userInitiated) {
                let fileExists = FileManager.default.fileExists(atPath: url.path)
                guard fileExists else { return nil }
                return NSImage(contentsOf: url)
            }.value

            // task 被 id 变化取消时,这里的赋值会被跳过 —— SwiftUI 不会渲染陈旧值。
            if let loaded {
                image = loaded
                isPlaceholder = false
            } else if isPlaceholder {
                // 大图加载失败但缩略图在,就保留缩略图当兜底,但补充错误信息给开发者。
                let fileExists = FileManager.default.fileExists(atPath: url.path)
                errorDetails = "源文件加载失败 (存在: \(fileExists))"
                print("[LocalLargeImageView] 加载失败: \(url.path), 存在: \(fileExists)")
            } else {
                let fileExists = FileManager.default.fileExists(atPath: url.path)
                errorDetails = "文件不存在或无权限读取"
                failed = true
                print("[LocalLargeImageView] 加载失败: \(url.path), 存在: \(fileExists)")
            }
        }
    }
}
