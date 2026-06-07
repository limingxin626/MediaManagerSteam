//
//  MediaPreviewDestination.swift
//  MyNote
//
//  NavigationStack destination for media preview — Hashable so NavigationStack
//  can distinguish different preview sessions and refresh the window title on
//  page change.
//

import SwiftUI

/// 引用语义的 Int 包装 — 每次 openPreview 重新创建,避免跨多次打开时旧值串扰。
final class IndexBox {
    var value: Int
    init(value: Int) { self.value = value }
}

struct MediaPreviewDestination: Hashable {
    /// 每一次推入都是全新的 identity,用于 NavigationStack 区分不同 session。
    let id = UUID()

    /// 全量媒体列表的快照引用。
    let mediaList: [Media]
    /// 进入预览时的起始索引。
    let startIndex: Int
    /// 双向绑定 — 翻页时 MediaDetailView 写回,外层据其同步 selectedIndex。
    var currentIndexBinding: Binding<Int>?

    var title: String {
        guard mediaList.indices.contains(startIndex) else { return "媒体预览" }
        return mediaList[startIndex].filePath.components(separatedBy: "/").last ?? "媒体预览"
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: MediaPreviewDestination, rhs: MediaPreviewDestination) -> Bool {
        lhs.id == rhs.id
    }
}