## 1. Navigation Infrastructure

- [ ] 1.1 新建 `MediaPreviewDestination.swift` — 实现 `Hashable`,持有 `mediaList: [Media]`、`startIndex: Int`,提供 `title: String` computed property(返回当前项的 basename 或 "媒体预览")
- [ ] 1.2 `MediaLibraryView` 外层包 `NavigationStack`,添加 `@State private var navigationPath = NavigationPath()`
- [ ] 1.3 `NavigationStack` 绑定 `.navigationDestination(for: MediaPreviewDestination.self)` 渲染 `MediaDetailView`

## 2. MediaLibraryView Integration

- [ ] 2.1 删除本地 `@State private var previewItems: [Media]?` 和 `@State private var previewIndex: Int` 状态
- [ ] 2.2 删除 body 中 `if let items = previewItems { MediaDetailView ... }` 的 overlay 渲染逻辑
- [ ] 2.3 `openPreview(at:)` 改为 `navigationPath.append(MediaPreviewDestination(mediaList: viewModel.loadedFlatItems, startIndex: index))`
- [ ] 2.4 `closePreview()` 改为 `navigationPath.removeLast()`;同步 `selectedIndex = currentIndex`(通过传入 MediaDetailView 的 onClose 回调获取)
- [ ] 2.5 `MediaDetailView` 的 `onClose` 回调传入 `closePreview`

## 3. MediaDetailView Adjustments

- [ ] 3.1 删除 `MediaDetailView` 中 hardcode 的 `.frame(minWidth:idealWidth:...)` 约束(如果仍存在)
- [ ] 3.2 保留 chrome 自动隐藏逻辑(NSEvent mouseMoved monitor、`scheduleHide` task、`chromeVisible`)
- [ ] 3.3 ESC/Space/× 关闭行为通过 `onClose` 回调向外传递,外层处理 pop

## 4. Window Title Sync

- [ ] 4.1 `MediaPreviewDestination.title` 读取 `mediaList[startIndex]` 的 basename,翻页后 startIndex 变化时 title 自动更新
- [ ] 4.2 确认 `MediaDetailView` 翻页时重建 destination 对象导致 NavigationStack title刷新

## 5. Verification

- [ ] 5.1 Xcode build 通过
- [ ] 5.2 双击 cell 打开预览 — 确认同一窗口内页面切换、标题栏显示文件名
- [ ] 5.3 ←/→ 翻页 — 确认标题栏同步更新
- [ ] 5.4 鼠标静止 1.5s — 确认 chrome 淡出
- [ ] 5.5 按 ESC 或返回 — 确认回到媒体库、选中态同步