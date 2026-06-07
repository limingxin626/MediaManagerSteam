## Context

Mac 端目前的 `MediaLibraryView` 在双击 cell 时,把 `MediaDetailView` 挂在 `.sheet(isPresented:)` 里(`MediaLibraryView.swift:77-84`),媒体列表和 `currentIndex` 通过 `@Binding` 直接在同一窗口里传。这种结构有两个固有问题:

1. sheet 永远受主窗口尺寸约束 —— 即便用户拉大主窗口,sheet 本身在 macOS 上也只占内部一块矩形,无法触发原生全屏(menu bar 一直在);
2. `MediaDetailView` 自己 hardcode 了 `frame(minWidth: 900, idealWidth: 1100, …)`(`MediaDetailView.swift:63-64`)是为了对抗 `Image.scaledToFit` 的 intrinsic-size 撑窗,带来的代价是不同比例的图永远塞在固定矩形里、有黑边。

参考实现:macOS 自带 Photos.app 与 Quick Look(空格唤起)都是「新开一个独立窗口 → 立刻进 native fullscreen → 鼠标静止后 chrome 自动隐藏」的模式。SwiftUI 14+ 提供 `Window` scene + `openWindow`/`dismissWindow` + `NSWindow.toggleFullScreen` 三件套,足以原生实现这个体验,不需要引入 AppKit window controller。

约束:
- Mac 端定位是只读浏览(CLAUDE.md「Mac is read-only in first phase」),不能引入会让窗口变重的写路径
- 不能引入新 SPM 依赖(项目方针)
- 必须保留现有键盘交互(←/→/Space/ESC)与翻页方向语义

## Goals / Non-Goals

**Goals:**
- 双击/空格打开预览时,新开一个**独立窗口**并立即进入 macOS 原生全屏(占满显示器、隐藏菜单栏)
- 体验对齐 Photos.app:黑色背景、chrome(顶部信息栏 + 底部 metadata)在鼠标静止 ~2s 后自动淡出,鼠标移动重新淡入
- ESC / Cmd+W 关闭预览窗口,焦点回到媒体库主窗口,主窗口 `selectedIndex` 与预览中最后看到的那张同步
- 移除 `MediaDetailView` 中 hardcode 的 `minWidth/idealWidth/minHeight/idealHeight` —— 由全屏窗口本身约束尺寸,图自由地 `scaledToFit` 到屏幕
- 翻页方向、键盘快捷键、视频播放器生命周期等既有行为完全不变

**Non-Goals:**
- 不做「窗口 / 全屏切换」按钮(macOS 标准绿色信号灯由系统提供,我们只决定**默认状态**是全屏)
- 不做多窗口/多预览实例(同时只允许一个预览窗口,再次双击新项目复用同一窗口、刷新内容)
- 不重写 `MediaDetailView` 的内部布局(header / 图 / metadata 三段不变,只是壳变了)
- 不动 Vue / Electron / Android 路径 —— 这是 Mac 端独有的体验差异
- 不引入「迷你播放器」「画中画」等额外模式

## Decisions

### Decision 1: 用 SwiftUI `Window` scene + `openWindow`,不自建 NSWindowController

把预览做成一个独立的 `Window` scene,挂在 `MyNoteApp` 里,绑定一个 ID(例如 `"media-preview"`)。从主窗口通过 `@Environment(\.openWindow)` 调用 `openWindow(id: "media-preview")` 触发。

**为何不**:
- ❌ 直接用 `.fullScreenCover`:macOS 上没有,iOS-only。
- ❌ AppKit `NSWindowController` + 自建 `NSWindow`:能做,但要写一堆 lifecycle、escape 默认行为(SwiftUI Window scene 已经处理 Cmd+W、聚焦、Dock 等),不值得。
- ❌ 在主窗口里 `presentationDetents(.fullScreen)`:macOS sheet 不支持 full screen detent。
- ✅ `Window` scene:声明式、零样板、和系统全屏(menu bar auto-hide、绿色信号灯)行为天然兼容。

副作用:`Window` scene 不能像 `.sheet` 那样直接 `@Binding`,数据要通过 SwiftUI Environment / 共享 `ObservableObject` 跨 scene 传(下条决策)。

### Decision 2: 跨窗口共享一个 `MediaPreviewSession`(`ObservableObject`)

新建 `MediaPreviewSession`(`@MainActor` 单例或挂在 `@StateObject` 上、用 `.environmentObject` 注入两个 scene):

```swift
@MainActor
final class MediaPreviewSession: ObservableObject {
    @Published var mediaList: [Media] = []
    @Published var currentIndex: Int = 0
    @Published var isOpen: Bool = false   // 当前预览窗口是否在显示
    func present(items: [Media], at index: Int) { … }
    func close() { isOpen = false }
}
```

主窗口双击时:
1. `session.present(items: viewModel.loadedFlatItems, at: globalIndex)`
2. `openWindow(id: "media-preview")`

预览窗口的 root view 监听 `session.$currentIndex`,渲染 `MediaDetailView`(下面会改造它,见 Decision 4)。

关闭预览时(用户按 ESC、Cmd+W,或点关闭按钮):
1. 预览窗口的 view 把当前 `session.currentIndex` 已经写回(双向)
2. `dismissWindow(id: "media-preview")` + `session.isOpen = false`
3. 主窗口的 `MediaLibraryView` 已经有 `onChange(of: showDetail)` 把 `selectedIndex = detailIndex` 同步过 —— 现在改成 `onChange(of: session.isOpen)`,逻辑等价

**为何不**用 SwiftUI Environment 直接传值:Environment 不能跨 scene 写回(单向),而我们需要预览窗口翻页后主窗口能同步。

**为何不**用全局 singleton:`ObservableObject` 注入更显式,易测试;且 `MyNoteApp` 用 `@StateObject` 持有,与 SwiftUI 生命周期绑定。

### Decision 3: 启动时即进入原生全屏(`NSWindow.toggleFullScreen`)

`Window` scene 本身没有声明式 API 让窗口「以全屏状态启动」。方案:

```swift
.onAppear {
    // 在 view appear 后下一帧找到自己的 NSWindow 并 toggleFullScreen
    DispatchQueue.main.async {
        if let win = NSApp.windows.first(where: { $0.identifier?.rawValue == "media-preview" }),
           !win.styleMask.contains(.fullScreen) {
            win.toggleFullScreen(nil)
        }
    }
}
```

辅助:`.windowStyle(.hiddenTitleBar)` + `.windowResizability(.contentSize)` 让窗口在非全屏瞬间看起来不那么突兀(用户用绿色信号灯退出全屏后看到的是无标题栏的浮窗,而不是带 chrome 的标准窗)。

**风险**:macOS 用户偏好里关掉了「使用单独的 Space 显示全屏」时,行为仍是 native fullscreen,只是不切 Space。可接受。

### Decision 4: `MediaDetailView` 改造 —— 移除固定 frame、加 chrome 自动隐藏

当前实现里的两块要改:

1. **删除** `.frame(minWidth: 900, idealWidth: 1100, maxWidth: .infinity, minHeight: 600, idealHeight: 760, maxHeight: .infinity)`(`MediaDetailView.swift:63-64`)。fullscreen window 本身就把窗口撑到屏幕,这层限制反而成了枷锁。

2. **新增** chrome 自动隐藏:

   ```swift
   @State private var chromeVisible: Bool = true
   @State private var lastMouseMove: Date = .now
   // 用 Timer.publish(every: 0.5) 检查;或 NSEvent.addLocalMonitorForEvents(.mouseMoved) 重置 lastMouseMove
   // chromeVisible 用 .opacity 控制 header / metadata,withAnimation(.easeInOut(duration: 0.25))
   ```

   阈值定 1.5s(Photos.app 实测约 1.5–2s);页面切换、按键操作时也算「活动」,顺手重置计时器。

   **不**用 `.onHover` —— 全屏视图覆盖整屏,hover 永远是 true,起不到作用。用 `NSEvent.addLocalMonitorForEvents(.mouseMoved)`,在 `.onAppear` 注册 / `.onDisappear` 注销。

### Decision 5: ESC 行为 = 关闭窗口(由 system 顺便退出全屏)

`Window` scene + native fullscreen 下,Cmd+W / 关闭按钮关闭窗口时系统会自动先退出全屏再关。不用我们手动 `toggleFullScreen`。

ESC 当前在 `MediaDetailView.keyboardShortcuts` 里调用 `dismiss()`(`MediaDetailView.swift:222-223`)—— 改成调 `session.close()` + `dismissWindow(id:)`。Space 同样保留「关闭」语义(`MediaDetailView.swift:226-228`),与网格态「空格打开」对称。

### Decision 6: 同时只有一个预览窗口

SwiftUI `Window`(不是 `WindowGroup`)scene 天然单实例 —— 再次 `openWindow(id:)` 会把现有窗口前置而不是新开。配合 `session.present()` 在打开前更新数据,实现「在主窗口点不同的 cell → 同一预览窗口换内容并 focus」。

## Risks / Trade-offs

- [全屏切换有一瞬可见的非全屏窗口] → 接受;`.hiddenTitleBar` + 黑底让这一帧很难察觉。若真有用户反馈,后备方案是在 `Window` scene 外层用 AppKit `NSWindow` 子类,override `makeKeyAndOrderFront` 直接以 fullscreen styleMask 创建。先不做。
- [`NSEvent.addLocalMonitorForEvents` 是全局 monitor,可能影响其他窗口] → 用 `addLocalMonitorForEvents` 限定本进程;只在预览 view `onAppear` 注册、`onDisappear` 立刻 remove。不会泄漏。
- [跨窗口 `ObservableObject` 状态同步在 macOS 多 Space 时可能延迟] → SwiftUI Environment-injected ObservableObject 在同一 process 内同步;Space 切换不影响。已验证过类似模式(Xcode、Photos.app 等都这么用)。
- [移除 `MediaDetailView` 固定 frame 后,如果回退到 sheet 用法会立刻被 Image intrinsic size 撑飞] → 接受;原先 sheet 用法的所有调用点都会改成 `Window` scene 路径,不存在「混用」的中间态。新增一行注释说明这块儿尺寸现在交由外部 scene 控制。
- [`MediaLibraryViewModel.loadedFlatItems` 是引用快照,预览翻到末尾时主窗口不一定还在线触发 loadMore] → 已知;现状 sheet 也是 `hasMore: false`(`MediaLibraryView.swift:82`),本次不动该行为。后续需要时再单独提案。

## Migration Plan

非 breaking 的 UI 行为变更,不涉及数据迁移。落地路径:
1. 加 `MediaPreviewSession`(纯新文件)
2. `MyNoteApp` 新增 `Window` scene 并注入 session(主窗口同时注入)
3. `MediaLibraryView` 把 `.sheet` 改成 `session.present(...) + openWindow(id:)`,删除 `@State showDetail/detailIndex`(改为读 session)
4. `MediaDetailView` 删固定 frame、改 ESC/Space 路径、加 chrome 自动隐藏
5. Xcode 跑一遍,人工验:双击进全屏 / ←→ 翻页 / 鼠标静止 chrome 淡出 / ESC 关闭 / 主窗口选中同步

无 rollback 顾虑(本地变更,git revert 即可)。

## Open Questions

- chrome 自动隐藏阈值是 1.5s 还是 2.0s?**默认 1.5s**(更贴近 Quick Look),若手感不好再调
- 预览窗关闭后是否需要主窗口自动 scroll-into-view 新 `selectedIndex`?**复用现有逻辑**(`MediaLibraryView.swift:102-105` 的 `onChange(of: selectedIndex)` 已经会调 `ensureMediaVisible`),不额外做
