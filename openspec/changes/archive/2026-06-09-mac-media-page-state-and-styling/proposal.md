## Why

Mac 端「媒体」tab 当前有两个体验问题:

1. **状态丢失** —— 在媒体网格里滚到中间,切到「主页」或「消息」再切回,网格回到顶部,刚加载好的远期桶也要重新加载。原因:`ContentView` 用 `switch selectedTab` 渲染对应 view,tab 切换时旧 view 树被销毁,`MediaLibraryView` 的 `@StateObject` 重新初始化,`MediaLibraryViewModel` 重建,`loadInitial()` 把 `scrollTop` 归零并清空 `bucketCache`。NSScrollView 本身也被销毁。

2. **样式瑕疵** —— 媒体网格区域有一圈蓝色边框 + 一根垂直滚动条。蓝色边框来自 `MediaLibraryView.grid` 上的 `.focusable(true)` —— SwiftUI 在 macOS 上对 focusable 的 view 默认会画系统蓝色 focus ring(NSFocusRingPlacement.below),即使 view 已经持焦,描边仍可见。滚动条来自 `NSScrollViewBridge` 创建的 `NSScrollView` 默认开了 `hasVerticalScroller = true`。Finder / Photos / Music 这类原生 Mac app 的网格区域既无外边框、也无滚动条,只在用户实际滚动时短暂出现 overlay 滚动条;目前的样式看起来「不像 Mac」。

## What Changes

- **修复 tab 切换状态丢失** —— `ContentView` 不再用 `switch` 销毁/重建 view 树,改为保持三个 tab 的 view 始终在层级中(主页/消息当前是 `*PlaceholderView`,开销可忽略),通过可见性/可交互性控制显示哪一个;媒体页的 `MediaLibraryView` 走同一路径后,`scrollTop` / `bucketCache` / 选中态都能在切回时保持
- **去掉媒体网格的蓝色 focus ring** —— `.focusable(true)` 上加 `.focusEffectDisabled(true)`(macOS 14+)。键盘焦点本身保留(方向键/空格仍然工作),只把系统默认的可见描边关掉
- **去掉媒体网格的垂直滚动条** —— `NSScrollViewBridge` 里把 `hasVerticalScroller` 改为 `false`,`autohidesScrollers` 改为 `true`(对没显示的滚动条冗余但保留以防未来改回),scrollerStyle 保留 `.overlay`

## Capabilities

### New Capabilities
<!-- 无新增 capability。本次只修复既有 mac-media-grid-selection / mac-native-local-db-media-grid capability 范围内的样式/状态 bug。 -->

### Modified Capabilities
- `mac-media-grid-selection`: 补充「切 tab 后保留网格状态(滚动位置、选中项、桶缓存)」「网格无可见 focus ring」「网格无可见滚动条」三条行为约束
- `mac-native-local-db-media-grid`: 补充「NSScrollView 滚动条默认隐藏」

## Impact

- `MyNote/MyNote/ContentView.swift` —— 改用 ZStack 持三个 view,根据 selectedTab 切可见性
- `MyNote/MyNote/MediaLibraryView.swift` —— `.focusable(true)` 后追加 `.focusEffectDisabled(true)`
- `MyNote/MyNote/NSScrollViewBridge.swift` —— `hasVerticalScroller` 默认改为 `false`
- 不影响 backend、Vue、Android、Electron
- 不影响 `MediaDetailView` 行为
- 不影响 `SidebarView` 行为
