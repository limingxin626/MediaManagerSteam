//
//  MediaPreviewWindowView.swift
//  MyNote
//
//  独立的全屏预览窗口 root view —— 主窗口 openWindow(id: "media-preview") 触发后,
//  这个 view 出现 → 立刻把承载它的 NSWindow 切换到 macOS 原生全屏。
//
//  数据来源:跨 scene 注入的 MediaPreviewSession(主窗口在 openWindow 之前已经
//  调过 session.present(items:at:))。窗口本身的尺寸由 Window scene 控制,
//  MediaDetailView 内部不再设固定 frame,媒体可以铺满整个屏幕。
//

import SwiftUI
import AppKit

struct MediaPreviewWindowView: View {
    @EnvironmentObject private var session: MediaPreviewSession

    var body: some View {
        // 黑色背景填满整个窗口 —— 全屏时即整个屏幕,退出全屏后即整个浮窗。
        ZStack {
            Color.black
                .ignoresSafeArea()

            MediaDetailView(
                mediaList: session.mediaList,
                currentIndex: Binding(
                    get: { session.currentIndex },
                    set: { session.currentIndex = $0 }
                ),
                hasMore: false,
                onNeedMore: { /* 桶按需加载,详情翻页时如果到末尾再考虑 */ }
            )
        }
        .onAppear {
            // Window scene 没有声明式 API 让窗口「以全屏状态启动」,只能在 view appear 后
            // 下一帧抓到 NSWindow 再 toggleFullScreen。延一帧是因为此时窗口可能还没进 windows 列表。
            DispatchQueue.main.async {
                enterFullScreenIfNeeded()
            }
        }
        .onDisappear {
            // 兜底:用户点系统红色信号灯 / Cmd+Q / Dock 关闭等路径下,
            // session.close() 不会被显式调用,这里把状态同步过去,
            // 让主窗口的 onChange(of: session.isOpen) 能正确同步选中态。
            session.isOpen = false
        }
    }

    /// 找到当前预览窗口(identifier == "media-preview"),如果还没进入全屏就切过去。
    /// 已经在全屏就什么都不做(避免重复 openWindow 时再 toggle 把它切回浮窗)。
    private func enterFullScreenIfNeeded() {
        guard let win = NSApp.windows.first(where: {
            $0.identifier?.rawValue == "media-preview"
        }) else { return }
        if !win.styleMask.contains(.fullScreen) {
            win.toggleFullScreen(nil)
        }
    }
}
