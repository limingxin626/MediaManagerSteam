//
//  MediaDetailView.swift
//  MyNote
//
//  媒体详情视图 - 图片大图 / 视频内嵌播放。读本地文件,不走 HTTP。
//  支持左右键 / 按钮在列表内切换上一张/下一张,切到末尾时触发 loadMore。
//

import SwiftUI
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

    @Environment(\.dismiss) private var dismiss
    /// 视频播放器随当前 media 重建,切换时旧 player 自动释放。
    @State private var player: AVPlayer? = nil

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
            header

            Divider()

            // 媒体本体 + 左右翻页热区
            ZStack {
                Color.black.opacity(0.9)
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
        }
        .frame(minWidth: 720, minHeight: 540)
        // 不可见的快捷键按钮 —— 提供 ←/→/ESC 全局响应。
        .background(keyboardShortcuts)
        .onAppear { rebuildPlayer() }
        .onChange(of: currentIndex) { _, _ in rebuildPlayer() }
        .onDisappear { player?.pause(); player = nil }
    }

    // MARK: - Header

    private var header: some View {
        HStack(spacing: 12) {
            Text(current?.filePath.components(separatedBy: "/").last ?? "")
                .font(.headline)
                .lineLimit(1)

            if !mediaList.isEmpty {
                Text("\(currentIndex + 1) / \(mediaList.count)\(hasMore ? "+" : "")")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Button(action: { dismiss() }) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 20))
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.plain)
        }
        .padding()
    }

    // MARK: - Content

    @ViewBuilder
    private var content: some View {
        if let media = current {
            if let url = media.localFileURL {
                if let mime = media.mimeType, mime.hasPrefix("video/") {
                    if let player {
                        VideoPlayer(player: player)
                    } else {
                        placeholder("视频加载中…")
                    }
                } else if let mime = media.mimeType, mime.hasPrefix("image/") {
                    // 大图独立加载,不复用 LocalImageLoader 的缩略图缓存
                    // (key 都是 mediaId,共用会让大图覆盖缩略图缓存,反而拖慢网格)
                    LocalLargeImageView(media: media, fileURL: url)
                } else {
                    placeholder("不支持的媒体类型: \(media.mimeType ?? "未知")")
                }
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
    }

    // MARK: - Keyboard

    /// 用一组隐藏按钮承载快捷键,SwiftUI 上这是最稳的全局快捷方式。
    private var keyboardShortcuts: some View {
        ZStack {
            Button("Prev", action: goPrev)
                .keyboardShortcut(.leftArrow, modifiers: [])
                .hidden()
            Button("Next", action: goNext)
                .keyboardShortcut(.rightArrow, modifiers: [])
                .hidden()
            Button("Close") { dismiss() }
                .keyboardShortcut(.escape, modifiers: [])
                .hidden()
        }
        .allowsHitTesting(false)
    }

    // MARK: - Navigation

    private func goPrev() {
        guard canGoPrev else { return }
        currentIndex -= 1
    }

    private func goNext() {
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

/// 大图视图:在后台线程解码,避免主线程卡顿。
/// 不接入 LocalImageLoader 共享缓存 —— 大图体积大,且 mediaId 会和缩略图 key 冲突。
/// task(id:) 在 media 切换时自动取消上一个,这是关键。
private struct LocalLargeImageView: View {
    let media: Media
    let fileURL: URL

    @State private var image: NSImage? = nil
    @State private var failed = false

    var body: some View {
        ZStack {
            if let image {
                Image(nsImage: image)
                    .resizable()
                    .scaledToFit()
            } else if failed {
                VStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 36))
                        .foregroundColor(.gray)
                    Text("无法加载图片")
                        .foregroundColor(.gray)
                    Text(fileURL.path)
                        .font(.caption)
                        .foregroundColor(.gray)
                        .textSelection(.enabled)
                }
            } else {
                ProgressView()
            }
        }
        .task(id: media.id) {
            image = nil
            failed = false
            let url = fileURL
            let loaded: NSImage? = await Task.detached(priority: .userInitiated) {
                guard FileManager.default.fileExists(atPath: url.path) else { return nil }
                return NSImage(contentsOf: url)
            }.value
            // task 被 id 变化取消时,这里的赋值会被跳过 —— SwiftUI 不会渲染陈旧值。
            if let loaded {
                image = loaded
            } else {
                failed = true
            }
        }
    }
}
