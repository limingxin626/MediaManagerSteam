## Context

`MediaLibraryView` 当前是个简单的 `LazyVGrid` + `onTapGesture { showDetail = true }` —— 单击立刻把 sheet 推上来。Mac 用户预期的是 Finder/Photos 的两段式交互：单击只是「指针选中」，再按空格或双击才打开预览，方向键可以在网格内移动选中。

技术上要解决三件事：
1. 选中态与预览态分离 —— 一个 `@State var selectedIndex: Int?`，与现有 `showDetail` 并列
2. 网格响应键盘 —— SwiftUI 的 `LazyVGrid` 默认不接受键盘焦点，要靠 `focusable()` + `.focused()` + `onKeyPress`
3. 选中项的滚动跟随 —— `ScrollViewReader` + `scrollTo(id)`，确保用方向键走到屏幕外的项时自动滚动

## Goals / Non-Goals

**Goals:**
- 单击网格项只选中（出现蓝色描边），不打开预览
- 双击网格项打开预览（与今天单击行为等价）
- 网格获得焦点时，按空格切换预览开/关
- 方向键 ←/→ 在网格内左右移动选中（跨行的边界处理：行首按 ← 跳到上一行末，行末按 → 跳到下一行首）
- 方向键 ↑/↓ 在网格内上下移动选中（按列对齐）
- 选中项滑出可视区时，`ScrollViewReader` 自动滚动让它可见
- 首屏加载完成后默认选中第 0 项

**Non-Goals:**
- 多选（Shift/Cmd+click）—— 这是后续功能，本次只做单选
- 拖拽 / 右键菜单 / Cmd+Delete 删除 —— 第一期只读
- 预览态内的键盘行为变更 —— `MediaDetailView` 现有的 ←/→/ESC 不动
- 选中状态持久化（刷新后保留）—— 重新打开 app 回到默认第 0 项即可
- 跨视图焦点（如从过滤按钮 Tab 到网格）—— 假设网格首次出现即获得焦点

## Decisions

### Decision 1: selectedIndex 放在 View 本地 `@State`，不进 ViewModel

**选择**：`@State private var selectedIndex: Int? = nil` 放在 `MediaLibraryView` 里。

**理由**：选中态是纯 UI 状态，跟数据加载、过滤、分页都不耦合。放进 `MediaLibraryViewModel` 会让 ViewModel 多一个跟业务无关的属性，还会让单元测试更难写。SwiftUI 社区共识也是「selection 默认放 View，跨视图共享时再上提」。

**取舍**：未来如果要做「打开 app 时恢复上次选中」，就得上提到 ViewModel + UserDefaults。本次明确不做。

### Decision 2: 用 `onKeyPress` 而不是隐藏 `Button + keyboardShortcut`

**选择**：在 grid 外层加 `.focusable(true).focused($gridFocused).onKeyPress { ... }`。

**理由**：
- `MediaDetailView` 用的是隐藏 Button + `keyboardShortcut` 方案，那里是为了在 sheet 内拦截全局快捷键
- 网格场景下要响应 4 个方向键 + 空格，写 5 个隐藏按钮代码量大且不直观
- `onKeyPress` (macOS 14+) 是 SwiftUI 原生的键盘事件入口，返回 `.handled` / `.ignored` 控制冒泡，更清晰
- 项目部署目标已是 macOS 14+（webp 解码要求），不会引入新的版本门槛

**取舍**：`onKeyPress` 要求 view 处于焦点链中，首次进入页面要主动 `gridFocused = true`，且过滤按钮一旦被点击会抢走焦点 —— 这是已知行为，acceptable（点完按钮再点一下网格就回来）。

### Decision 3: 双击用 SwiftUI 的 `TapGesture(count: 2)` + `.simultaneously(with:)`

**选择**：
```swift
.onTapGesture(count: 2) { openDetail(at: index) }
.onTapGesture(count: 1) { selectedIndex = index }
```
SwiftUI 会自动处理双击优先 —— 单击事件被延迟 `NSEvent.doubleClickInterval` 等待第二击，没等到才触发。

**理由**：标准做法。比手写 `DispatchQueue.main.asyncAfter` 去判断双击稳得多。

**取舍**：单击会有约 200ms 延迟才触发选中高亮 —— 这是 macOS 系统级行为，Finder/Photos 也一样，用户对这个延迟有预期。

### Decision 4: 方向键的网格几何 —— 按列数硬算

**选择**：网格列数 `columns = 4` 是已知常量（写死在 View 里），所以方向键移动用纯算术：
- `→`：`selectedIndex + 1`（到末项停住，不 wrap）
- `←`：`selectedIndex - 1`（到 0 停住）
- `↓`：`selectedIndex + 4`（超过 count - 1 时夹到 count - 1）
- `↑`：`selectedIndex - 4`（小于 0 时夹到 0）

**理由**：4 列写死在 `columns` 数组里，没必要从 layout 反查实际渲染的列数。如果将来引入可变列数（用户调节缩略图大小），再把 `columns.count` 提成属性即可。

**取舍**：不实现 wrap-around（末项按 → 跳回首项）—— Finder 也不 wrap，符合预期。

### Decision 5: 自动滚动用 `ScrollViewReader` + 项目 id

**选择**：把 `ScrollView` 套在 `ScrollViewReader { proxy in ... }` 里，`selectedIndex` 变化时 `proxy.scrollTo(media.id, anchor: .center)`。

**理由**：`LazyVGrid` 配 `ScrollViewReader` 是 SwiftUI 推荐的滚动到指定项方案，`anchor: .center` 让选中项尽量居中可见，行为对用户最直观。

**取舍**：`LazyVGrid` 滚到没渲染过的项时会先实例化它再滚动，可能有一帧延迟 —— acceptable。

### Decision 6: 空格键的 fallback —— 选中为空时按空格打开第一项

**选择**：
```swift
case .space:
    if showDetail { dismiss preview }
    else if let idx = selectedIndex { open at idx }
    else if !media.isEmpty { selectedIndex = 0; open at 0 }
```

**理由**：避免用户首次进入还没点过任何项时按空格毫无反应。这条 fallback 让空格永远「做点什么」。

### Decision 7: 预览打开时空格关闭 —— 怎么传递？

**选择**：`MediaDetailView` 自己也在 `keyboardShortcuts` 里加一个空格 → `dismiss()`。不依赖 `MediaLibraryView` 拦截。

**理由**：sheet 内的焦点链与底层 view 是分开的，外层 `.onKeyPress` 在 sheet present 时收不到事件。让 sheet 自己处理空格关闭最干净，跟现有 ESC 关闭对称。

## Risks / Trade-offs

- **[Risk] 过滤按钮点击会抢走网格焦点** → Mitigation：用户点完按钮再点一下网格区域即可恢复。第一版不引入复杂的焦点管理，观察实际使用后再加。
- **[Risk] `onKeyPress` 在 macOS 14 以下不可用** → Mitigation：项目已要求 macOS 14+（webp），不影响。
- **[Risk] 双击的 200ms 延迟让单击高亮显得「迟钝」** → Mitigation：这是系统行为，Finder/Photos 一样；不修。
- **[Risk] `LazyVGrid` 中未渲染的项滚动到时机** → Mitigation：`scrollTo` 配 `LazyVGrid` 是官方支持模式；如果实测有问题，回退到 `scrollTo` 后 `DispatchQueue.main.async` 再 `scrollTo` 一次的微 hack。
- **[Risk] 加载更多时 selectedIndex 越界** → Mitigation：`selectedIndex` 只在用户主动按键时变化，loadMore 只 append 不删项，索引不会失效；删除/过滤切换会触发 loadInitial，届时把 selectedIndex 重置为 0（或 nil 再 onAppear 设 0）。
