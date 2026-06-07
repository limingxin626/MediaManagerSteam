//
//  MediaTypeFilter.swift
//  MyNote
//
//  媒体库 toolbar 筛选 Picker 的类型枚举,供 Picker tag / Binding 桥接使用。
//  rawValue 与 MediaLibraryViewModel.selectedMediaType(String?) 对齐:
//  - nil ↔ .all
//  - "image" ↔ .image
//  - "video" ↔ .video
//

import Foundation

enum MediaTypeFilter: String, Hashable, CaseIterable, Identifiable {
    case all
    case image
    case video

    var id: String { rawValue }

    var title: String {
        switch self {
        case .all: return "全部"
        case .image: return "图片"
        case .video: return "视频"
        }
    }
}
