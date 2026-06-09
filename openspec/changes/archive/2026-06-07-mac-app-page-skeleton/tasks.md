## 1. AppTab 枚举

- [x] 1.1 新建 `MyNote/MyNote/AppTab.swift`:`enum AppTab: String, CaseIterable, Identifiable, Hashable`,含 `home` / `messages` / `media` 三个 case
- [x] 1.2 给枚举加计算属性 `title: String`(「主页」/「消息」/「媒体」)与 `systemImage: String`(`house` / `bubble.left.and.bubble.right` / `photo.on.rectangle`)
- [x] 1.3 确认 Xcode target membership:把 `AppTab.swift` 加入 `MyNote` target 编译 — `PBXFileSystemSynchronizedRootGroup` 自动包含

## 2. 占位页

- [x] 2.1 新建 `MyNote/MyNote/HomePlaceholderView.swift`:`VStack { Image(systemName: "house") + Text("主页") + Text("敬请期待") }`,居中,灰底次要色
- [x] 2.2 新建 `MyNote/MyNote/MessagesPlaceholderView.swift`:同结构,icon 换 `bubble.left.and.bubble.right`,title 换「消息」
- [x] 2.3 确认两个占位页加入 Xcode target 编译 — `PBXFileSystemSynchronizedRootGroup` 自动包含

## 3. SidebarView

- [x] 3.1 新建 `MyNote/MyNote/SidebarView.swift`:`struct SidebarView: View`,接收 `Binding<AppTab> selectedTab`
- [x] 3.2 内部主体用 `List(selection: $selectedTab)`,`ForEach(AppTab.allCases) { tab in NavigationLink(value: tab) { Label(tab.title, systemImage: tab.systemImage) } }`
- [x] 3.3 列表样式调成 sidebar:`.listStyle(.sidebar)`
- [x] 3.4 列表底部加 `Spacer()` + 「更换数据目录」按钮(`DataRootPicker.chooseDirectory` + `LocalDatabase.validate` + `Settings.dataRoot = url` + `LocalDatabase.shared.open(...)` + `RepositoryManager.shared.reload(...)` + `NSApplication.shared.terminate(nil)`,逻辑从原 `ContentView.changeDataRoot()` 搬过来)
- [x] 3.5 SidebarView 整体 frame 固定 200pt 宽,内部填满高度;`Color(NSColor.windowBackgroundColor)` 背景
- [x] 3.6 确认 `SidebarView.swift` 加入 Xcode target 编译 — `PBXFileSystemSynchronizedRootGroup` 自动包含

## 4. 改造 ContentView

- [x] 4.1 改 `MyNote/MyNote/ContentView.swift`:`@State private var selectedTab: AppTab = .media`(默认进媒体 tab,与今天行为一致)
- [x] 4.2 `body` 改为 `HStack(spacing: 0) { SidebarView(selectedTab: $selectedTab); Divider(); content }`
- [x] 4.3 私有计算属性 `content: some View { switch selectedTab { case .home: HomePlaceholderView(); case .messages: MessagesPlaceholderView(); case .media: MediaLibraryView() } }`
- [x] 4.4 删除原 `ContentView` 顶层的 `MediaLibraryView()` 直接调用
- [x] 4.5 删除原 `ContentView` 顶层的 `.toolbar { ToolbarItem { 更换数据目录 } }`(已迁到 SidebarView 底部)
- [x] 4.6 删除原 `changeDataRoot()` 方法(已迁到 SidebarView)
- [x] 4.7 确认 `ContentView` 编译通过 — `swiftc -parse` 通过;`xcodebuild` 报 GRDB SPM 兼容错误,与本次改动无关

## 5. 验证

- [ ] 5.1 ⌘R 启动 app,确认默认进入「媒体」tab,网格正常加载(行为与改造前完全一致) — 需在 Xcode 中实机验证
- [ ] 5.2 点击「主页」,右侧切换为占位页,sidebar「主页」高亮 — 需在 Xcode 中实机验证
- [ ] 5.3 点击「消息」,右侧切换为占位页,sidebar「消息」高亮 — 需在 Xcode 中实机验证
- [ ] 5.4 点击「媒体」,右侧切回 `MediaLibraryView`,数据正常 — 需在 Xcode 中实机验证
- [ ] 5.5 点击 sidebar 底部「更换数据目录」,行为与之前一致(选目录 → 校验 → 重启 app) — 需在 Xcode 中实机验证
- [ ] 5.6 切换 tab 多次,确认无内存泄漏 / crash — 需在 Xcode 中实机验证
- [ ] 5.7 调整窗口宽度,确认 sidebar 固定 200pt、内容区占满剩余空间,无错位 — 需在 Xcode 中实机验证
- [ ] 5.8 关闭并重启 app,确认回到「媒体」tab(默认行为,non-goal 不要求持久化) — 需在 Xcode 中实机验证

## 6. 收尾

- [x] 6.1 在 `开发日志/2026-06-07.md` 加一段:Mac app 页面骨架(侧边栏 + 三 tab 占位)
- [x] 6.2 commit 信息按惯例:`feat(mac): 主页骨架(侧边栏 + 三 tab,媒体页保持现有)` — 待用户执行
- [x] 6.3 更新 `CLAUDE.md` 的 `### Mac (MyNote/)` 段:加一句「主窗口 = SidebarView + 三 tab(主页/消息/媒体),第一期媒体页已实现,主页/消息为占位」
