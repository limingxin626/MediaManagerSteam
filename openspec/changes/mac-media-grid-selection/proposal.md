## Why

Mac 端 `MediaLibraryView` 目前只有「点击直接打开预览」这一种交互。当用户想浏览大量媒体并只看其中几张时，每次都要打开 sheet → 关闭 → 再点击下一张，体验很重。Finder 和 macOS 「照片」app 的标准做法是：单击选中（不打开），方向键在网格里上下左右移动选中，空格键打开/退出预览。Mac 用户对这套键盘语义有强烈的肌肉记忆，缺失会显得这个 app「不够 Mac」。

## What Changes

- 给 `MediaLibraryView` 增加「选中态」（selected index），与「预览态」（showDetail）解耦：单击只选中，不打开预览
- 双击网格项打开预览（保留原「单击直接打开」的体验路径，但通过双击触发）
- 空格键在网格视图中切换预览的打开/关闭（预览打开时按空格关闭，关闭时按空格打开当前选中项）
- 方向键 ←/→/↑/↓ 在网格中移动选中项，并自动滚动让选中项进入可视区
- 选中项在网格中以蓝色描边 + 背景高亮显示（贴近 Finder/Photos 的 selection ring 样式）
- 网格加载首屏完成后，默认选中第 0 项（避免空选中态下按方向键无响应）

## Capabilities

### New Capabilities
- `mac-media-grid-selection`: Mac 端媒体网格的选中态与键盘导航行为（单击选中、双击预览、方向键移动选中、空格切换预览）

### Modified Capabilities
<!-- 现有 specs 都是前端 Web/PWA 端的预览/缩略图行为，不涉及 Mac 网格选中。本次新增独立 capability,不修改既有 spec。 -->

## Impact

- `MyNote/MyNote/MediaLibraryView.swift` — 网格加 selection state、键盘响应、双击手势、选中描边样式
- `MyNote/MyNote/MediaLibraryViewModel.swift` — 新增 `selectedIndex` 状态（也可放在 View 本地 `@State`，design 阶段决定）
- 不影响 backend、Vue、Android、Electron
- 不影响 `MediaDetailView` 的内部行为（它仍然管自己的左右切换 + ESC 关闭）
