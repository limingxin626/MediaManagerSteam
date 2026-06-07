## 1. 状态与高亮(单击选中)

- [x] 1.1 在 `MediaLibraryView` 中新增 `@State private var selectedIndex: Int? = nil`
- [x] 1.2 在 `MediaGridItem` 中接收 `isSelected: Bool` 参数,选中时在 ZStack 外层叠加蓝色 `RoundedRectangle().stroke(Color.accentColor, lineWidth: 3)`(选用 accent color 以贴合系统外观)
- [x] 1.3 将 grid `ForEach` 中的 `.onTapGesture { ... showDetail = true }` 改为 `.onTapGesture(count: 1) { selectedIndex = index }` + `.onTapGesture(count: 2) { selectedIndex = index; detailIndex = index; showDetail = true }`(双击在前会被 SwiftUI 自动优先识别)
- [x] 1.4 给 `MediaGridItem` 传 `isSelected: selectedIndex == index`,验证单击后描边出现、双击直接打开预览

## 2. 默认选中与重载重置

- [x] 2.1 在 `loadInitial()` 完成后(`MediaLibraryView` 用 `.onChange(of: viewModel.media)` 或在 `loadInitial` 末尾)如果 `selectedIndex == nil && !media.isEmpty`,设为 0
- [x] 2.2 在 `changeMediaType` / `toggleStarredOnly` 触发 `loadInitial` 后,把 `selectedIndex` 重置为 0(若新结果空则为 nil)。为不破坏 ViewModel 纯度,通过 View 层的 `onChange(of: viewModel.selectedMediaType)` 或 `onChange(of: viewModel.showOnlyStarred)` 来重置

## 3. 键盘焦点

- [x] 3.1 在 `MediaLibraryView` 中新增 `@FocusState private var gridFocused: Bool`
- [x] 3.2 给 `grid` 外层(`ScrollView` 上方或下方)挂 `.focusable(true).focused($gridFocused)`,并在 `.onAppear` 中 `gridFocused = true`
- [ ] 3.3 验证页面首次出现时网格已获得焦点,过滤按钮被点击后焦点会丢失(已知行为)

## 4. 方向键导航

- [x] 4.1 把网格列数 4 提取为 `private let columnCount = 4`,`columns` 用 `Array(repeating: GridItem(.flexible(), spacing: 8), count: columnCount)` 生成
- [x] 4.2 在持焦 view 上挂 `.onKeyPress` 处理 `.leftArrow / .rightArrow / .upArrow / .downArrow`,实现:
  - `→`: `selectedIndex = min((selectedIndex ?? -1) + 1, media.count - 1)`
  - `←`: `selectedIndex = max((selectedIndex ?? 1) - 1, 0)`
  - `↓`: `selectedIndex = min((selectedIndex ?? -columnCount) + columnCount, media.count - 1)`
  - `↑`: `selectedIndex = max((selectedIndex ?? columnCount) - columnCount, 0)`
  - 处理 `selectedIndex == nil` 时:任一方向键设为 0(若 `media` 非空),返回 `.handled`
  - `media.isEmpty` 时返回 `.ignored`,不消费事件
- [ ] 4.3 验证四个方向键在网格内移动选中描边正确,且不会越界或 wrap-around

## 5. 自动滚动

- [x] 5.1 把 `grid` 中的 `ScrollView` 包进 `ScrollViewReader { proxy in ScrollView { ... } }`
- [x] 5.2 给 `MediaGridItem` 所在的 ForEach cell 加 `.id(mediaItem.id)`(已经用了 `id: \.element.id` 做 ForEach key,这是隐式 id,仍需显式 `.id()` 让 `scrollTo` 找得到)
- [x] 5.3 在 `MediaLibraryView` body 上挂 `.onChange(of: selectedIndex) { _, newValue in if let i = newValue, viewModel.media.indices.contains(i) { withAnimation { proxy.scrollTo(viewModel.media[i].id, anchor: .center) } } }`
- [ ] 5.4 验证用方向键走到屏幕外的项时,ScrollView 自动滚动让其进入可视区

## 6. 空格键切换预览

- [x] 6.1 在 grid 的 `.onKeyPress` 中加 `.space` 分支:
  - 若 `showDetail == true`: 不在网格层处理,让事件冒泡给 sheet(返回 `.ignored`)
  - 若 `showDetail == false && selectedIndex != nil`: `detailIndex = selectedIndex!; showDetail = true`,返回 `.handled`
  - 若 `showDetail == false && selectedIndex == nil && !media.isEmpty`: `selectedIndex = 0; detailIndex = 0; showDetail = true`,返回 `.handled`
  - 若 `media.isEmpty`: 返回 `.ignored`
- [x] 6.2 在 `MediaDetailView.keyboardShortcuts` 中新增一个隐藏 Button:`Button("Close on space") { dismiss() }.keyboardShortcut(.space, modifiers: []).hidden()`,与现有 ESC 关闭对称
- [x] 6.3 在 `MediaLibraryView` 的 `.sheet` 关闭回调中(可用 `.onChange(of: showDetail)` 监听变 false),把 `selectedIndex = detailIndex` —— 预览中用户左右切换到的最后一张,回到网格仍保持选中
- [ ] 6.4 验证:网格态按空格 → 打开预览;预览态按空格 → 关闭预览且选中项是预览最后看的那张

## 7. 联调与回归

- [ ] 7.1 用方向键 + 空格快速浏览大量媒体,确认无延迟、滚动跟随顺畅
- [ ] 7.2 切换「图片/视频/全部」筛选,确认选中项重置到第 0 项
- [ ] 7.3 测试到达列表末尾再按 →/↓ 时触发 loadMore(目前 loadMore 由 `if viewModel.hasMore { ... .onAppear ... }` 触发,确认方向键走到该 placeholder cell 时也能触发 —— 若否,后续可在 4.2 的 → / ↓ 处加 `if newIndex >= media.count - columnCount { Task { await viewModel.loadMore() } }`,本任务列入观察项)
- [ ] 7.4 验证双击直接打开预览时,网格的选中项也会同步(便于关闭后回到该项)
- [ ] 7.5 验证 `MediaDetailView` 内部 ←/→/ESC 仍然正常工作,未被新空格 shortcut 干扰

## 8. 开发日志

- [x] 8.1 在项目根目录的开发日志中追加本次变更(每天一篇日志的规则),记录:Mac 端媒体网格新增 Finder 风格选中态(单击选中、双击预览、方向键移动、空格切换预览)
