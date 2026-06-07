//
//  NSScrollViewBridge.swift
//  MyNote
//
//  VirtualScrollView — 自建 NSScrollView 桥接 SwiftUI 内容。
//
//  为什么不用 SwiftUI ScrollView + 找 enclosingScrollView 的桥:
//    - .background() 里的 NSView 在不同 macOS 版本里挂在的子树位置不一致,
//      superview 链经常断在 _NSHostingView / _NSScrollViewWrapper,拿不到 NSScrollView。
//    - 即使偶然拿到了,SwiftUI ScrollView 的 contentView bounds 通知也可能因为
//      Autolayout/StackView 包装而不被转发到我们注册的 selector。
//    - 一旦回写链断,scrollTop 永远是 0,所有派生的 visibleBuckets / currentDate 都失效。
//
//  这里我们直接 new 一个 NSScrollView,把 SwiftUI 内容塞进 documentView(NSHostingView),
//  这样 NSScrollView 引用一直在手里,bounds 监听 100% 收得到,
//  程序化 scroll 也直接对自己的实例调用,不会有失联问题。
//

import SwiftUI
import AppKit

struct VirtualScrollView<Content: View>: NSViewRepresentable {
    /// 内容总高度。documentView 的 frame.height 用它,撑出滚动条比例。
    let contentHeight: CGFloat
    /// 当前实时滚动位置(由桥回写)。
    @Binding var scrollTop: CGFloat
    /// 视口高度回写(由桥反测)。
    @Binding var viewportHeight: CGFloat
    /// 容器宽度回写(由桥反测,= clip.bounds.width)。
    @Binding var containerWidth: CGFloat
    /// 程序化跳转触发计数器:每次变化就跳到 targetY。
    let jumpTrigger: Int
    /// 跳转目标 y 坐标。
    let targetY: CGFloat
    /// SwiftUI 内容构造闭包(绝对定位的 ZStack)。
    @ViewBuilder var content: () -> Content

    func makeCoordinator() -> Coordinator {
        Coordinator(
            scrollTop: $scrollTop,
            viewportHeight: $viewportHeight,
            containerWidth: $containerWidth
        )
    }

    func makeNSView(context: Context) -> NSScrollView {
        let sv = NSScrollView()
        sv.hasVerticalScroller = true
        sv.hasHorizontalScroller = false
        sv.autohidesScrollers = true
        sv.scrollerStyle = .overlay
        sv.drawsBackground = false
        sv.borderType = .noBorder
        sv.verticalScrollElasticity = .allowed
        sv.horizontalScrollElasticity = .none
        sv.translatesAutoresizingMaskIntoConstraints = false

        // documentView: NSHostingView 包 SwiftUI 内容,翻转坐标 → (0,0) 在左上
        let host = FlippedHostingView(rootView: AnyView(content()))
        host.translatesAutoresizingMaskIntoConstraints = false
        sv.documentView = host

        let clip = sv.contentView
        clip.postsBoundsChangedNotifications = true
        clip.postsFrameChangedNotifications = true

        // 初始 frame:host 至少铺满一屏
        let initialW = max(clip.bounds.width, 1)
        let initialH = max(contentHeight, 1)
        host.frame = NSRect(x: 0, y: 0, width: initialW, height: initialH)

        // 关联 coordinator + 挂监听
        let coord = context.coordinator
        coord.scrollView = sv
        NotificationCenter.default.addObserver(
            coord,
            selector: #selector(Coordinator.boundsDidChange(_:)),
            name: NSView.boundsDidChangeNotification,
            object: clip
        )
        NotificationCenter.default.addObserver(
            coord,
            selector: #selector(Coordinator.frameDidChange(_:)),
            name: NSView.frameDidChangeNotification,
            object: clip
        )

        // 首次报告一次 viewport / 宽度(等一拍让 Autolayout 给到真实 bounds)
        DispatchQueue.main.async {
            coord.reportViewportIfChanged(sv.contentView.bounds.height)
            coord.reportWidthIfChanged(sv.contentView.bounds.width)
        }

        return sv
    }

    func updateNSView(_ sv: NSScrollView, context: Context) {
        let coord = context.coordinator
        guard let host = sv.documentView as? FlippedHostingView<AnyView> else { return }

        // 每次 update 都把新 Content 推给 NSHostingView —— NSHostingView.rootView 是可写属性,
        // 赋值后内部 SwiftUI 走 diff,只更新变化部分(LocalThumbView 的 .task(id:) 不会重启,
        // NSCache 命中的图片不重解码),滚动期间频繁 update 也不会让缩略图闪烁。
        // 这里**不能**加 contentHeight 守卫 —— 滚动和 bucketCache 更新都不改 contentHeight,
        // 守卫会把这些更新都吞掉,导致视图卡在旧快照上,看起来就是空白。
        host.setRootView(AnyView(content()))

        // 同步 documentView 尺寸:宽度跟 clip,高度跟 contentHeight
        let clipW = sv.contentView.bounds.width
        let targetH = max(contentHeight, sv.contentView.bounds.height)
        if abs(host.frame.width - clipW) > 0.5 || abs(host.frame.height - targetH) > 0.5 {
            host.frame = NSRect(x: 0, y: 0, width: max(clipW, 1), height: max(targetH, 1))
        }

        // 程序化跳转
        if coord.lastJumpTrigger != jumpTrigger {
            coord.lastJumpTrigger = jumpTrigger
            DispatchQueue.main.async {
                coord.jumpTo(targetY)
            }
        }
    }

    static func dismantleNSView(_ nsView: NSScrollView, coordinator: Coordinator) {
        NotificationCenter.default.removeObserver(coordinator)
    }

    // MARK: - Coordinator

    /// 注意:不要标 @MainActor。selector 触发线程不可控,
    /// 内部用 DispatchQueue.main.async 写回 @Binding。
    final class Coordinator: NSObject {
        @Binding var scrollTop: CGFloat
        @Binding var viewportHeight: CGFloat
        @Binding var containerWidth: CGFloat
        weak var scrollView: NSScrollView?
        var lastJumpTrigger: Int = .min
        /// 程序化跳转时屏蔽一次回写,避免 jump → boundsChange → setScrollTop 抖动
        var suppressFeedback: Bool = false
        private var lastReportedTop: CGFloat = -1
        private var lastReportedViewport: CGFloat = -1
        private var lastReportedWidth: CGFloat = -1

        init(
            scrollTop: Binding<CGFloat>,
            viewportHeight: Binding<CGFloat>,
            containerWidth: Binding<CGFloat>
        ) {
            self._scrollTop = scrollTop
            self._viewportHeight = viewportHeight
            self._containerWidth = containerWidth
        }

        @objc func boundsDidChange(_ note: Notification) {
            guard let clip = note.object as? NSClipView else { return }
            let y = clip.documentVisibleRect.origin.y
            DispatchQueue.main.async { [weak self] in
                guard let self else { return }
                if self.suppressFeedback {
                    self.suppressFeedback = false
                    return
                }
                if abs(y - self.lastReportedTop) < 0.5 { return }
                self.lastReportedTop = y
                self.scrollTop = y
            }
        }

        @objc func frameDidChange(_ note: Notification) {
            guard let clip = note.object as? NSClipView else { return }
            let h = clip.bounds.height
            let w = clip.bounds.width
            DispatchQueue.main.async { [weak self] in
                self?.reportViewportIfChanged(h)
                self?.reportWidthIfChanged(w)
            }
        }

        func reportViewportIfChanged(_ h: CGFloat) {
            if abs(h - lastReportedViewport) < 0.5 { return }
            lastReportedViewport = h
            viewportHeight = h
        }

        func reportWidthIfChanged(_ w: CGFloat) {
            if abs(w - lastReportedWidth) < 0.5 { return }
            lastReportedWidth = w
            containerWidth = w
        }

        func jumpTo(_ y: CGFloat) {
            guard let sv = scrollView else { return }
            let clip = sv.contentView
            let docHeight = sv.documentView?.bounds.height ?? 0
            let viewportH = clip.bounds.height
            let maxY = max(0, docHeight - viewportH)
            let clamped = max(0, min(y, maxY))
            suppressFeedback = true
            clip.scroll(to: NSPoint(x: 0, y: clamped))
            sv.reflectScrolledClipView(clip)
            // 立即同步本地状态
            lastReportedTop = clamped
            scrollTop = clamped
        }
    }
}

// MARK: - 翻转坐标系的 NSHostingView

/// 用 NSView 包住 NSHostingView,翻转坐标系使 (0,0) 在左上,
/// 与 SwiftUI 的 .offset(x:y:) 语义一致。避免直接 override NSHostingView.isFlipped。
private final class FlippedHostingView<Content: View>: NSView {
    private var hostingView: NSHostingView<Content>

    init(rootView: Content) {
        hostingView = NSHostingView(rootView: rootView)
        super.init(frame: .zero)
        addSubview(hostingView)
    }

    @MainActor required dynamic init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override var isFlipped: Bool { true }

    func setRootView(_ rootView: Content) {
        // 直接更新 rootView 属性 —— NSHostingView 内部会 diff,只重渲染变化的部分,
        // 缩略图 NSCache 命中时不会重解码,也就不会闪烁。
        // 千万不要 removeFromSuperview + new NSHostingView,那会让整个 SwiftUI 树销毁重建,
        // 所有 LocalThumbView 的 .task 重新跑一遍,闪烁就在这。
        hostingView.rootView = rootView
    }

    override func layout() {
        super.layout()
        hostingView.frame = bounds
    }
}
