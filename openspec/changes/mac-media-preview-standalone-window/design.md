## Context

Mac 端 `MediaLibraryView` 当前双击 cell 时把 `MediaDetailView` 以 overlay 形式渲染在 ZStack 顶层 —— 底层网格、工具栏、DateScrubber 仍透过半透明层可见。窗口标题栏始终显示"媒体库",不反映预览中的文件名。

本次变更的目标是:**在同一窗口内做页面级切换(preview 替换媒体库内容),窗口标题栏实时显示当前媒体文件名**。

约束:
- Mac 端只读定位,不改写操作路径
- 无新 SPM 依赖,仅 SwiftUI
- 保留现有键盘交互(←/→/Space/ESC)与翻页方向语义
- 始终只有一个 OS 窗口

## Goals / Non-Goals

**Goals:**
- 双击/空格打开预览时,同一窗口内内容切换为预览视图(NavigationStack push 风格)
- 窗口标题栏实时显示当前媒体文件名(basename of `filePath`)
- ESC/返回按钮关闭预览,回到媒体库,`selectedIndex` 已同步
- 鼠标静止 ~1.5s 后 chrome 自动淡出,鼠标移动重新淡入
- `MediaDetailView` 移除 hardcode 固定 frame

**Non-Goals:**
- 不新开 OS 窗口
- 不做全屏(用户可通过系统绿色信号灯自行全屏)
- 不重写 `MediaDetailView` 内部布局(header/图/metadata 三段不变)
- 不动 Vue/Electron/Android路径

## Decisions

### Decision 1: 用 `NavigationStack` 做单窗口页面切换,不自建 state

`MediaLibraryView` 外层包 `NavigationStack`,双击时 `navigationPath` 推入 `MediaPreviewDestination`,预览关闭时 pop。

```swift
@State private var navigationPath = NavigationPath()

// 双击时
navigationPath.append(MediaPreviewDestination(mediaList: viewModel.loadedFlatItems, startIndex: globalIndex))

// 预览关闭时
navigationPath.removeLast()
```

**为何不**:
- ❌ Overlay(ZStack): 当前实现,问题是底层内容仍可见
- ❌ `fullScreenCover` / 新 Window: 会新开 OS 窗口,用户要求单窗口
- ✅ `NavigationStack` push: 天然单窗口页面切换,title跟随当前 destination变化

### Decision 2: 窗口标题动态更新

`NavigationStack` 的 `.navigationTitle` 会读取被推入 destination 的类型名。给 `MediaPreviewDestination` 加自定义 `title` computed property 即可:

```swift
struct MediaPreviewDestination: Hashable {
    let mediaList: [Media]
    let startIndex: Int

    var title: String {
        guard mediaList.indices.contains(startIndex) else { return "媒体预览" }
        return mediaList[startIndex].filePath.components(separatedBy: "/").last ?? "媒体预览"
    }
}
```

翻页时因为 destination 对象变了(`currentIndex` 变了会重建新的 destination),`NavigationStack` 会自动刷新 title。

### Decision 3: `MediaDetailView` 通过 `@Binding` 接收 `currentIndex`

不再通过 `session` 跨窗口传,而是直接 `@Binding var currentIndex`。这样翻页时 `currentIndex` 变化,`MediaDetailView` 内部自动刷新,不需要额外状态同步。

`MediaPreviewDestination` 作为数据容器,把 `mediaList + currentIndex` 通过 binding传给 `MediaDetailView`。

### Decision 4: `MediaDetailView` 关闭时回调 `onClose`

```swift
let onClose: () -> Void
```

`onClose` 在 `MediaDetailView` 按 ESC/空格/× 时调用,外层收到后 `navigationPath.removeLast()`。

### Decision 5: 保留 chrome 自动隐藏逻辑

`MediaDetailView` 现有的 `NSEvent.addLocalMonitorForEvents(.mouseMoved)` + `chromeVisible` 逻辑原样保留。

## Risks / Trade-offs

- [翻页时 `NavigationStack` 标题不更新 — destination 的 Hashable identity 问题] → 翻页后 `currentIndex` 变化会生成新的 `MediaPreviewDestination`,NavigationStack 会认为这是新的 destination,触发 title 更新(已通过 Decision 2解决)
- [媒体库滚动位置在预览关闭后丢失] → 接受;NavigationStack push/pop 不保留子 view 状态,这是 iOS/macOS 通用行为