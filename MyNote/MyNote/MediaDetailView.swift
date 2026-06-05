//
//  MediaDetailView.swift
//  MyNote
//
//  媒体详情视图 - 图片大图 / 视频内嵌播放。读本地文件,不走 HTTP。
//

import SwiftUI
import AVKit

struct MediaDetailView: View {
    let media: Media
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // 顶部工具栏
            HStack {
                Text(media.filePath.components(separatedBy: "/").last ?? "")
                    .font(.headline)
                    .lineLimit(1)
                Spacer()
                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
                .keyboardShortcut(.escape, modifiers: [])
            }
            .padding()

            Divider()

            // 媒体本体
            content
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.black.opacity(0.9))

            // 元信息
            metadata
                .padding()
        }
        .frame(minWidth: 720, minHeight: 540)
    }

    @ViewBuilder
    private var content: some View {
        if let url = media.localFileURL {
            if let mime = media.mimeType, mime.hasPrefix("video/") {
                VideoPlayer(player: AVPlayer(url: url))
            } else if let mime = media.mimeType, mime.hasPrefix("image/") {
                if let image = NSImage(contentsOf: url) {
                    Image(nsImage: image)
                        .resizable()
                        .scaledToFit()
                } else {
                    placeholder("无法加载图片\n路径: \(url.path)\n原始 file_path: \(media.filePath)")
                }
            } else {
                placeholder("不支持的媒体类型: \(media.mimeType ?? "未知")")
            }
        } else {
            placeholder("数据目录未配置")
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

    private var metadata: some View {
        HStack(spacing: 24) {
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
        }
    }

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
