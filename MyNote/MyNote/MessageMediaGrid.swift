//
//  MessageMediaGrid.swift
//  MyNote
//
//  消息卡 / 详情面板内嵌的媒体网格。
//  布局规则(对齐 vue 端 MessageCard.vue / MessageDetail 的 3x3 宫格):
//    1 张   → 1x1 大图,占满卡宽
//    2 张   → 1x2 并排
//    3-9 张 → 3x3 平铺
//    > 9 张 → 前 9 张 + 1 个「+N」占位
//
//  缩略图渲染走 `LocalThumbView(media:)`,需要先把 `MessageMediaItem` 转成 `Media`。
//

import SwiftUI

struct MessageMediaGrid: View {
    let items: [MessageMediaItem]
    let onClick: (Int) -> Void
    /// 是否在 detail 面板内:detail 内 cell 直接触发预览;feed 内 cell
    /// 触发 onClick 让外层 selectMessage + 推 destination(本期 feed 内 cell
    /// 不直接进 preview,先开 detail,vue 端同款)。
    let clickBehavior: ClickBehavior

    enum ClickBehavior {
        case emitClick      // 调 onClick(index),由外层决定后续
        case directPreview  // 直接触发预览(详情面板用)
    }

    init(
        items: [MessageMediaItem],
        clickBehavior: ClickBehavior = .emitClick,
        onClick: @escaping (Int) -> Void = { _ in }
    ) {
        self.items = items
        self.clickBehavior = clickBehavior
        self.onClick = onClick
    }

    var body: some View {
        if items.isEmpty {
            EmptyView()
        } else {
            layoutView
        }
    }

    @ViewBuilder
    private var layoutView: some View {
        switch items.count {
        case 1:
            singleImage
        case 2:
            pairGrid
        case 3...9:
            squareGrid(columns: 3, showOverflowBadge: false, overflowCount: 0)
        default:
            squareGrid(columns: 3, showOverflowBadge: true, overflowCount: items.count - 9)
        }
    }

    // MARK: - 1 张大图

    private var singleImage: some View {
        Button(action: { onClick(0) }) {
            MessageThumbCell(media: items[0], isLarge: true)
                .aspectRatio(16.0/9.0, contentMode: .fill)
                .frame(maxWidth: .infinity)
                .clipped()
        }
        .buttonStyle(.plain)
    }

    // MARK: - 2 张并排

    private var pairGrid: some View {
        HStack(spacing: 2) {
            ForEach(0..<2, id: \.self) { idx in
                Button(action: { onClick(idx) }) {
                    MessageThumbCell(media: items[idx])
                        .aspectRatio(1, contentMode: .fill)
                        .frame(maxWidth: .infinity, maxHeight: 240)
                        .clipped()
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - 3x3 网格

    private func squareGrid(columns: Int, showOverflowBadge: Bool, overflowCount: Int) -> some View {
        let visible = Array(items.prefix(9))
        return LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 2), count: columns), spacing: 2) {
            ForEach(0..<visible.count, id: \.self) { idx in
                Button(action: { onClick(idx) }) {
                    MessageThumbCell(media: visible[idx])
                        .aspectRatio(1, contentMode: .fill)
                        .clipped()
                }
                .buttonStyle(.plain)
            }
            if showOverflowBadge {
                ZStack {
                    Color.black.opacity(0.55)
                    Text("+\(overflowCount)")
                        .font(.system(size: 24, weight: .semibold))
                        .foregroundColor(.white)
                }
                .aspectRatio(1, contentMode: .fill)
            }
        }
    }
}

// MARK: - 缩略图 cell

/// 媒体 cell 走 `LocalThumbView(media:)` 渲染,加一个右上角星标 + 视频图标覆盖层。
/// 视频 / 图片 行为与 `MediaGridItem` 同构(Media 域已实现),这里给消息域做
/// 简化版(只关心缩略图 + 视频标识 + 视频时长徽章,星标在 read-only 阶段恒为只读 view)。
struct MessageThumbCell: View {
    let media: MessageMediaItem
    var isLarge: Bool = false

    var body: some View {
        ZStack {
            // 缩略图:MessageMediaItem → Media 转换,给 LocalThumbView
            LocalThumbView(media: media.asMedia())

            // 视频标识 + 时长
            if let mime = media.mimeType, mime.hasPrefix("video/") {
                VStack {
                    Spacer()
                    HStack {
                        Image(systemName: "play.fill")
                            .font(.system(size: isLarge ? 14 : 10))
                            .foregroundColor(.white)
                            .padding(6)
                            .background(Color.black.opacity(0.5))
                            .clipShape(Circle())
                        Spacer()
                        if let durationMs = media.durationMs {
                            Text(formatDuration(durationMs))
                                .font(.system(size: isLarge ? 12 : 10))
                                .foregroundColor(.white)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.black.opacity(0.6))
                                .clipShape(Capsule())
                                .padding(6)
                        }
                    }
                }
            }

            // 视频中央播放图标(大图)
            if isLarge, let mime = media.mimeType, mime.hasPrefix("video/") {
                Image(systemName: "play.circle.fill")
                    .font(.system(size: 36))
                    .foregroundColor(.white)
                    .shadow(radius: 2)
            }
        }
    }

    private func formatDuration(_ ms: Int) -> String {
        let totalSeconds = ms / 1000
        let m = totalSeconds / 60
        let s = totalSeconds % 60
        return String(format: "%d:%02d", m, s)
    }
}

// MARK: - 转换工具

extension MessageMediaItem {
    /// 给 `LocalThumbView(media:)` 喂的 `Media` —— 复制本 item 已有字段。
    /// 与 `init(from media: Media)` 互为反操作,放在这里方便组件用 LocalThumbView
    /// 渲染消息域的缩略图,避免每个 cell 重复构造 Media。
    func asMedia() -> Media {
        Media(
            id: id,
            filePath: filePath,
            repoId: repoId,
            fileUrl: fileUrl,
            thumbPath: thumbPath,
            thumbUrl: thumbUrl,
            fileSize: nil,
            mimeType: mimeType,
            width: width,
            height: height,
            durationMs: durationMs,
            rating: 0,
            starred: starred,
            viewCount: 0,
            tags: tags,
            videoMediaId: nil,
            frameMs: nil,
            startMs: nil,
            endMs: nil,
            takenAt: nil,
            gpsLat: nil,
            gpsLng: nil,
            orientation: nil,
            cameraMake: nil,
            cameraModel: nil,
            lens: nil,
            videoCodec: nil,
            audioCodec: nil,
            hasAudio: nil,
            fps: nil,
            bitrate: nil,
            createdAt: createdAt,
            updatedAt: updatedAt
        )
    }
}
