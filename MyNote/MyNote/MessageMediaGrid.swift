//
//  MessageMediaGrid.swift
//  MyNote
//
//  消息卡内嵌的媒体网格 —— 用 Telegram 风格 mosaic 算法计算 layout(从
//  vue 端 `utils/mosaic.ts` 移植,见 `MessageMosaic.swift`)。
//
//  与 vue 端对齐的要点:
//    - 容器虚拟宽度 W = 400 算 layout(算法内部用),实际渲染时 SwiftUI
//      通过 GeometryReader 拿真实宽度,把所有 weight 按比例缩放到真实像素。
//    - 1 张:
//        · 竖图(ratio < 1):maxWidth = 600 * ratio,vue 原 cap(400~600pt)
//        · 横图(ratio >= 1):maxWidth = 500pt,Mac 端新增 — vue 不 cap,
//          但 Mac 容器宽,不 cap 会撑满整张 card 看着过宽
//        · aspectRatio 用夹紧后的 ratio
//    - 2 张:均为超宽且比例相近才上下排,否则按 ratio 加权一行内并排。
//      Mac 端新增整组 maxWidth = 500pt(同单图横图 cap),避免两张竖图
//      撑满宽度后每张 cell 高达 400+pt。
//    - 3+ 张:贪心搜索 partition,行高 / 列宽按 ratio 加权(3 张不再走 L 型)。
//    - > 10 张(对齐 vue 端 maxPreviewItems):在最后一张上叠 +N 徽章。
//
//  缩略图渲染走 `LocalThumbView(media:)`,需要先把 `MessageMediaItem` 转成 `Media`。
//

import SwiftUI

struct MessageMediaGrid: View {
    let mediaItems: [MessageMediaItem]
    let onClick: (Int) -> Void

    /// 算法用的虚拟容器宽度(对齐 vue 端 `MOSAIC_CONTAINER_WIDTH = 400`)
    private static let mosaicContainerWidth: Double = 800
    /// 单图竖图最大等效高度(对齐 vue 端 `MAX_SINGLE_IMAGE_HEIGHT = 600`)
    private static let maxSingleImageHeight: CGFloat = 600
    /// 单图横图最大宽度(Mac 端新增 — vue 端横图不限制,但 Mac 端 feed
    /// 容器比 vue 宽,如果不 cap 单图会撑满整张 card 看着过宽)
    private static let maxSingleLandscapeWidth: CGFloat = 500
    /// 缩略图 cell 之间的间隙
    private static let cellGap: CGFloat = 2
    /// feed 内最多预览几张(对齐 vue 端 `maxPreviewItems = 10`)
    private static let maxPreviewItems = 10

    // MARK: - 派生数据

    /// 渲染用的 items(超过 maxPreviewItems 的被截掉,只参与 overflowCount 计算)
    private var visibleItems: [MessageMediaItem] {
        Array(mediaItems.prefix(Self.maxPreviewItems))
    }

    private var overflowCount: Int {
        max(0, mediaItems.count - Self.maxPreviewItems)
    }

    /// 每张图的 width/height 比例。缺 width/height 时回落 1.5(对齐 vue 端 `mediaRatios` 默认值)
    private var ratios: [Double] {
        visibleItems.map { item in
            if let w = item.width, let h = item.height, h > 0 {
                return Double(w) / Double(h)
            }
            return 1.5
        }
    }

    /// 夹紧到 [0.667, 1.7] 后用于 layout 决策(超长图 / 超竖图不参与权重计算)
    private var clampedRatios: [Double] {
        ratios.map { min(1.7, max(0.667, $0)) }
    }

    private var layout: MosaicLayout {
        calculateMosaicLayout(
            ratios: ratios,
            containerWidth: Self.mosaicContainerWidth
        )
    }

    /// 单图的最大宽度。
    ///   - 竖图(ratio < 1):vue 原 cap = 600 * ratio,范围 400~600pt
    ///   - 横图(ratio >= 1):Mac 端新增 cap = 500pt(vue 端不 cap,但 Mac 容器宽,
    ///     不 cap 会撑满整张 card,看着过宽)
    private var singleImageMaxWidth: CGFloat? {
        guard visibleItems.count == 1 else { return nil }
        let ratio = clampedRatios[0]
        if ratio < 1 {
            return Self.maxSingleImageHeight * CGFloat(ratio)
        } else {
            return Self.maxSingleLandscapeWidth
        }
    }

    /// 2 张图时整组的最大宽度。Mac 端新增 — vue 不 cap,但 2 张竖图在
    /// Mac 宽容器下不 cap 会让每张 cell 高达 400+pt,看着过宽。
    /// 取同单图横图一样的 500pt(每张 250pt),保持 cap 体系一致。
    private var twoImageMaxWidth: CGFloat? {
        guard visibleItems.count == 2 else { return nil }
        return Self.maxSingleLandscapeWidth
    }

    /// 整体最大宽度(单图 / 2 张图走 cap,3+ 张不 cap)
    private var overallMaxWidth: CGFloat? {
        singleImageMaxWidth ?? twoImageMaxWidth
    }

    /// 整个 mosaic 容器在虚拟宽度 400 下的宽高比。SwiftUI 用 `.aspectRatio(_, contentMode: .fit)`
    /// 保持这个比例,所有 weight 按真实宽度等比缩放。
    private var containerAspectRatio: CGFloat {
        if visibleItems.count == 1 {
            return CGFloat(clampedRatios[0])
        }
        let virtualW = Self.mosaicContainerWidth
        let totalH = layout.rows.reduce(0.0) { $0 + $1.heightWeight }
        return totalH > 0 ? CGFloat(virtualW / totalH) : 16.0 / 9.0
    }

    // MARK: - body

    var body: some View {
        if mediaItems.isEmpty {
            EmptyView()
        } else {
            GeometryReader { geo in
                let actualW = geo.size.width
                layoutView(actualWidth: actualW)
            }
            .aspectRatio(containerAspectRatio, contentMode: .fit)
            .frame(maxWidth: overallMaxWidth ?? .infinity, alignment: .leading)
        }
    }

    // MARK: - 布局分发

    @ViewBuilder
    private func layoutView(actualWidth: CGFloat) -> some View {
        rowsLayout(actualWidth: actualWidth)
    }

    // MARK: - rows 布局(1 / 2 / 3+ 张通用)

    @ViewBuilder
    private func rowsLayout(actualWidth: CGFloat) -> some View {
        let virtualW = Self.mosaicContainerWidth
        let totalVirtualH = layout.rows.reduce(0.0) { $0 + $1.heightWeight }
        let gaps = CGFloat(max(0, layout.rows.count - 1)) * Self.cellGap
        // 真实总高 = (虚拟总高 / 虚拟宽) * 真实宽 - 间隙
        let actualH = CGFloat(totalVirtualH / virtualW) * actualWidth - gaps
        let heightWeights: [CGFloat] = layout.rows.map { row in
            let ratio = row.heightWeight / totalVirtualH
            return CGFloat(ratio) * actualH
        }

        VStack(spacing: Self.cellGap) {
            ForEach(Array(layout.rows.enumerated()), id: \.offset) { rowIdx, row in
                rowView(
                    row: row,
                    rowHeight: heightWeights[rowIdx],
                    actualWidth: actualWidth
                )
            }
        }
    }

    @ViewBuilder
    private func rowView(row: MosaicRow, rowHeight: CGFloat, actualWidth: CGFloat) -> some View {
        let totalWeight = row.items.reduce(0.0) { $0 + $1.widthWeight }
        let gaps = CGFloat(max(0, row.items.count - 1)) * Self.cellGap
        let availableW = actualWidth - gaps
        HStack(spacing: Self.cellGap) {
            ForEach(Array(row.items.enumerated()), id: \.element.index) { _, item in
                let cellW = availableW * CGFloat(item.widthWeight / totalWeight)
                cellView(mediaIndex: item.index)
                    .frame(width: cellW, height: rowHeight)
                    .clipped()
            }
        }
    }

    // MARK: - 单个 cell

    @ViewBuilder
    private func cellView(mediaIndex: Int) -> some View {
        let item = visibleItems[mediaIndex]
        let isLastVisible = mediaIndex == visibleItems.count - 1 && overflowCount > 0

        Button(action: { onClick(mediaIndex) }) {
            ZStack {
                MessageThumbCell(media: item)
                if isLastVisible {
                    overflowBadge
                }
            }
        }
        .buttonStyle(.plain)
    }

    private var overflowBadge: some View {
        ZStack {
            Color.black.opacity(0.55)
            Text("+\(overflowCount)")
                .font(.system(size: 24, weight: .semibold))
                .foregroundColor(.white)
        }
    }
}

// MARK: - 缩略图 cell

/// 媒体 cell 走 `LocalThumbView(media:)` 渲染,加视频图标覆盖层 + 视频时长徽章。
/// 星标在 read-only 阶段不在此渲染(消息卡整体底部已有星标)。
struct MessageThumbCell: View {
    let media: MessageMediaItem

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
                            .font(.system(size: 10))
                            .foregroundColor(.white)
                            .padding(6)
                            .background(Color.black.opacity(0.5))
                            .clipShape(Circle())
                        Spacer()
                        if let durationMs = media.durationMs {
                            Text(formatDuration(durationMs))
                                .font(.system(size: 10))
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
