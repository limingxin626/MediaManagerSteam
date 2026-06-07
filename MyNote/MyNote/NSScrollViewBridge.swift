//
//  NSScrollViewBridge.swift
//  MyNote
//
//  SwiftUI ScrollView ↔ AppKit NSScrollView 的桥。两个用途:
//    1. 反向回写:实时把 NSScrollView 的 documentVisibleRect.origin.y 喂给 SwiftUI 的 scrollTop。
//       SwiftUI 的 ScrollView 自身不暴露偏移监听 API,只能通过 AppKit 桥获取。
//    2. 程序化跳转:观察 jumpTrigger 变化时,直接调 contentView.scroll(to:) 跳到 targetY。
//       这条路径与子视图是否被实例化无关,所以「跳到从未渲染过的远期桶」也能命中。
//
//  使用方式:在 SwiftUI ScrollView 的 .background 里放一个 NSScrollViewBridge,
//  bridge 会在 willMoveToSuperview 时找到 enclosingScrollView 并挂监听。
//

import SwiftUI
import AppKit

struct NSScrollViewBridge: NSViewRepresentable {
    /// 当前实时滚动位置(由 bridge 回写)。
    @Binding var scrollTop: CGFloat
    /// 程序化跳转的触发计数(每次变化就重读 targetY 跳一次)。
    let jumpTrigger: Int
    /// 跳转目标 y 坐标。
    let targetY: CGFloat

    func makeCoordinator() -> Coordinator {
        Coordinator(scrollTop: $scrollTop)
    }

    func makeNSView(context: Context) -> NSView {
        let v = BridgeAnchorView()
        v.coordinator = context.coordinator
        v.translatesAutoresizingMaskIntoConstraints = false
        return v
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        let coord = context.coordinator
        // 第一次进来挂监听(必须在 superview / window 准备好之后)
        if coord.scrollView == nil, let bridge = nsView as? BridgeAnchorView {
            DispatchQueue.main.async {
                bridge.attachIfReady()
            }
        }
        // 跳转触发判定:只有 jumpTrigger 真的变了才执行,避免 update 来回触发死循环
        if coord.lastJumpTrigger != jumpTrigger {
            coord.lastJumpTrigger = jumpTrigger
            DispatchQueue.main.async {
                coord.jumpTo(targetY)
            }
        }
    }

    // MARK: - Coordinator

    @MainActor
    final class Coordinator: NSObject {
        @Binding var scrollTop: CGFloat
        weak var scrollView: NSScrollView?
        var lastJumpTrigger: Int = .min
        /// 程序化跳转时屏蔽一次回写,避免 jump → boundsChange → setScrollTop 形成抖动
        var suppressFeedback: Bool = false

        init(scrollTop: Binding<CGFloat>) {
            self._scrollTop = scrollTop
        }

        func attach(to sv: NSScrollView) {
            scrollView = sv
            sv.contentView.postsBoundsChangedNotifications = true
            NotificationCenter.default.addObserver(
                self,
                selector: #selector(boundsDidChange(_:)),
                name: NSView.boundsDidChangeNotification,
                object: sv.contentView
            )
        }

        deinit {
            NotificationCenter.default.removeObserver(self)
        }

        @objc func boundsDidChange(_ note: Notification) {
            guard let clip = note.object as? NSClipView else { return }
            if suppressFeedback {
                // 仅吞一次回写,然后立即放开
                suppressFeedback = false
                return
            }
            let y = clip.documentVisibleRect.origin.y
            // SwiftUI 主线程写
            DispatchQueue.main.async { [weak self] in
                self?.scrollTop = y
            }
        }

        func jumpTo(_ y: CGFloat) {
            guard let sv = scrollView else { return }
            let clip = sv.contentView
            let docHeight = sv.documentView?.bounds.height ?? 0
            let viewportH = clip.bounds.height
            let maxY = max(0, docHeight - viewportH)
            let clamped = max(0, min(y, maxY))
            // 屏蔽紧随而来的 boundsChange 一次,避免重复触发上层 dispatchFetches
            suppressFeedback = true
            clip.scroll(to: NSPoint(x: 0, y: clamped))
            sv.reflectScrolledClipView(clip)
        }
    }
}

// MARK: - Anchor View

/// 占位 NSView,只用来在加进 view tree 后找 enclosingScrollView。
private final class BridgeAnchorView: NSView {
    var coordinator: NSScrollViewBridge.Coordinator?

    override var intrinsicContentSize: NSSize { .zero }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        attachIfReady()
    }

    func attachIfReady() {
        guard let coord = coordinator, coord.scrollView == nil else { return }
        if let sv = findEnclosingScrollView() {
            coord.attach(to: sv)
        }
    }

    /// SwiftUI 的 ScrollView 实际是一个 NSScrollView 的内嵌结构;
    /// .background 里的 NSView 会被放进 ScrollView 的 documentView 子树,
    /// 标准的 enclosingScrollView 即可拿到。
    private func findEnclosingScrollView() -> NSScrollView? {
        var v: NSView? = superview
        while let cur = v {
            if let sv = cur as? NSScrollView { return sv }
            v = cur.superview
        }
        // SwiftUI 在某些版本里把 NSScrollView 包在 enclosingScrollView 属性外,兜一层
        return enclosingScrollView
    }
}
