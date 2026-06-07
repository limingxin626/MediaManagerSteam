//
//  MediaPreviewSession.swift
//  MyNote
//
//  跨窗口共享的预览状态:主窗口 (MediaLibraryView) 触发 present(...),
//  独立的预览 Window scene (MediaPreviewWindowView) 读取并渲染。
//
//  为什么不用 @Binding —— SwiftUI Window scene 之间无法像 sheet 那样直接传 binding,
//  ObservableObject 通过 .environmentObject 注入两个 scene 是最干净的双向同步路径。
//

import SwiftUI

@MainActor
final class MediaPreviewSession: ObservableObject {
    /// 预览要展示的列表(通常是 MediaLibraryViewModel.loadedFlatItems 的快照)。
    @Published var mediaList: [Media] = []
    /// 当前展示的索引,翻页会改它;主窗口在关闭时读它同步 selectedIndex。
    @Published var currentIndex: Int = 0
    /// 预览窗口是否在显示。openWindow/dismissWindow 由 view 负责,这里只标状态。
    /// 主窗口观察它的 false 边沿 → 把 currentIndex 同步回 selectedIndex。
    @Published var isOpen: Bool = false

    /// 主窗口调用:更新内容并标记打开。view 层紧跟着 openWindow(id:) 即可。
    func present(items: [Media], at index: Int) {
        mediaList = items
        currentIndex = max(0, min(index, max(items.count - 1, 0)))
        isOpen = true
    }

    /// 预览窗内 ESC/Cmd+W/Space 关闭时调用。view 层紧跟着 dismissWindow(id:)。
    /// onDisappear 也会兜底把 isOpen 置 false,防止外部关闭手势(红色信号灯)漏更新。
    func close() {
        isOpen = false
    }
}
