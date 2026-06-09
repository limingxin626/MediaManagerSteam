//
//  MessageMediaGrid5.swift
//  MyNote
//
//  消息卡内嵌的媒体网格 —— 简单 5 列等宽布局,每格 1:1 裁剪显示。
//
//  这是替换 `MessageMediaGrid`(telegram 风格 mosaic 布局)的临时版本;
//  原 mosaic 实现完整保留(见 `MessageMediaGrid.swift` + `MessageMosaic.swift`),
//  后续想切回复杂布局 / 自适应列数时,直接换回 MessageMediaGrid 即可。
//
//  设计要点:
//    - 5 列等宽,每行最多 5 张;cell 间距 2pt(对齐原 mosaic 视觉密度)
//    - 每格 1:1(缩略图按 1:1 裁剪,与 Media tab grid 风格保持一致)
//    - > maxPreviewItems(10)时,最后一张叠 +N 徽章(保留原 mosaic 行为)
//    - onClick 透传,调用方负责具体行为(消息卡目前 no-op)
//

import SwiftUI

struct MessageMediaGrid5: View {
    let mediaItems: [MessageMediaItem]
    let onClick: (Int) -> Void

    /// feed 内最多预览几张(对齐原 mosaic 的 `maxPreviewItems = 10`)
    private static let maxPreviewItems = 10
    /// 缩略图 cell 之间的间隙
    private static let cellGap: CGFloat = 2
    /// 5 列等宽
    private static let columnCount: Int = 5
    /// 单格 1:1 比例
    private static let cellAspect: CGFloat = 1.0

    /// 渲染用的 items(超过 maxPreviewItems 的被截掉,只参与 overflowCount 计算)
    private var visibleItems: [MessageMediaItem] {
        Array(mediaItems.prefix(Self.maxPreviewItems))
    }

    private var overflowCount: Int {
        max(0, mediaItems.count - Self.maxPreviewItems)
    }

    private var gridColumns: [GridItem] {
        Array(repeating: GridItem(.flexible(), spacing: Self.cellGap), count: Self.columnCount)
    }

    var body: some View {
        if mediaItems.isEmpty {
            EmptyView()
        } else {
            LazyVGrid(columns: gridColumns, spacing: Self.cellGap) {
                ForEach(Array(visibleItems.enumerated()), id: \.element.id) { index, _ in
                    cellView(mediaIndex: index)
                        .aspectRatio(Self.cellAspect, contentMode: .fill)
                        .clipped()
                }
            }
        }
    }

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
