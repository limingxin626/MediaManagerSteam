## 1. 新增 MediaPreviewSession (跨窗口共享状态)

- [x] 1.1 在 `MyNote/MyNote/` 新建 `MediaPreviewSession.swift`,实现 `@MainActor final class MediaPreviewSession: ObservableObject`,字段 `@Published var mediaList: [Media]`、`@Published var currentIndex: Int`、`@Published var isOpen: Bool`,方法 `present(items:at:)` 与 `close()`
- [x] 1.2 在 `MyNoteApp.swift` 顶层用 `@StateObject private var previewSession = MediaPreviewSession()` 创建实例,并通过 `.environmentObject(previewSession)` 注入到 `WindowGroup` 的 root

## 2. 新增独立预览 Window scene

- [x] 2.1 在 `MyNoteApp.body` 内追加一个 `Window("预览", id: "media-preview") { … }` scene,挂载新的 `MediaPreviewWindowView()`,同样 `.environmentObject(previewSession)`
- [x] 2.2 给该 scene 加 `.windowStyle(.hiddenTitleBar)` 与 `.windowResizability(.contentSize)`,让非全屏瞬间也是无 chrome 的浮窗
- [x] 2.3 在 `MyNote/MyNote/` 新建 `MediaPreviewWindowView.swift`:root 用黑色背景填满,内嵌改造后的 `MediaDetailView`,把 `session.mediaList` / `$session.currentIndex` 透传
- [x] 2.4 在 `MediaPreviewWindowView.onAppear` 通过 `DispatchQueue.main.async` 找到 `NSApp.windows` 里 `identifier == "media-preview"` 的窗口,如果 `!styleMask.contains(.fullScreen)` 就 `toggleFullScreen(nil)` 进全屏
- [x] 2.5 `MediaPreviewWindowView.onDisappear` 把 `session.isOpen` 置 false(防止用户点系统关闭按钮时状态漏更新)

## 3. 主窗口接入新预览路径

- [x] 3.1 `MediaLibraryView` 注入 `@EnvironmentObject var previewSession: MediaPreviewSession` 与 `@Environment(\.openWindow) var openWindow`
- [x] 3.2 删除 `@State private var detailIndex / showDetail` 以及 `.sheet(isPresented: $showDetail) { MediaDetailView(…) }` 整段
- [x] 3.3 双击 cell 的逻辑改为 `previewSession.present(items: viewModel.loadedFlatItems, at: globalIndex); openWindow(id: "media-preview")`(原 `showDetail = true` 处全部替换)
- [x] 3.4 空格键打开预览的逻辑(`handleKeyPress` 内 `.space` 分支)同样改为 `previewSession.present(…) + openWindow(…)`
- [x] 3.5 把原来的 `onChange(of: showDetail) { _, isShown in if !isShown { selectedIndex = detailIndex } }` 改成 `onChange(of: previewSession.isOpen) { _, isOpen in if !isOpen { selectedIndex = previewSession.currentIndex } }`,保留主窗口选中态同步

## 4. MediaDetailView 改造

- [x] 4.1 删除 `MediaDetailView.swift:63-64` 的 `.frame(minWidth: 900, idealWidth: 1100, maxWidth: .infinity, minHeight: 600, idealHeight: 760, maxHeight: .infinity)` 整行,补一行注释「尺寸由外层 Window scene 控制」
- [x] 4.2 把 `dismiss()` 的调用点(关闭按钮 `MediaDetailView.swift:88-94`、ESC `:222-223`、空格 `:226-228`)统一改为调用注入的 `previewSession.close()` + `dismissWindow(id: "media-preview")`(注入 `@Environment(\.dismissWindow)`),保留 `@Environment(\.dismiss)` 作为兜底以兼容预览(`#Preview`)
- [x] 4.3 新增 `@State private var chromeVisible: Bool = true`,把 `header` 与 `metadata` 视图各自包一层 `.opacity(chromeVisible ? 1 : 0).animation(.easeInOut(duration: 0.25), value: chromeVisible)`
- [x] 4.4 新增 `@State private var hideTask: Task<Void, Never>? = nil`;新增 `func scheduleHide()` —— cancel 旧 task,新开一个 `Task { try? await Task.sleep(for: .seconds(1.5)); if !Task.isCancelled { chromeVisible = false } }`
- [x] 4.5 在 `onAppear` 用 `NSEvent.addLocalMonitorForEvents(matching: .mouseMoved)` 注册监视器,回调里 `chromeVisible = true; scheduleHide()`;在 `onDisappear` 用 `NSEvent.removeMonitor(_:)` 移除,并 `hideTask?.cancel()`
- [x] 4.6 在 `goPrev` / `goNext` / `rebuildPlayer`(切换 media)函数末尾调 `chromeVisible = true; scheduleHide()`,让翻页和按键操作算作活动

## 5. 验收 / 手动测试

- [ ] 5.1 Xcode build & run,确认 app 启动正常,主窗口能进网格视图
- [ ] 5.2 双击任意 cell:验证新窗口立刻进入原生全屏(menu bar 隐藏、占满屏幕、黑底)
- [ ] 5.3 ←/→ 翻页:验证翻页方向动画保留(原有 `media-preview-navigation` 行为),chrome 在按键后保持显示并重新计时
- [ ] 5.4 鼠标静止 ~1.5s:验证顶部 header 与底部 metadata 淡出;移动鼠标:验证淡入
- [ ] 5.5 按 ESC:验证窗口先退出全屏再关闭,主窗口被前置,`selectedIndex` 已同步为预览中最后看到的索引
- [ ] 5.6 按 Cmd+W、空格分别测试关闭手势,行为与 ESC 一致
- [ ] 5.7 预览开着时回到主窗口再双击不同 cell:验证复用同一窗口、内容切换、依然全屏
- [ ] 5.8 关闭预览后主窗口若新 `selectedIndex` 不在可视范围,验证 `ensureMediaVisible` 自动滚入视野(复用既有逻辑)

## 6. 写开发日志

- [x] 6.1 在仓库的开发日志目录(按 MEMORY.md 约定「每天一篇日志」)追加今天的条目,记录本次改动的关键决策(独立 Window scene、跨窗口 ObservableObject、chrome 自动隐藏)与遇到的坑
