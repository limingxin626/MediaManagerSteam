## Why

Mac 端当前点开任意媒体是用 `.sheet` 弹出 `MediaDetailView`,被锚在主窗口里,最大也就是用户拉出来的那点尺寸,且每次 sheet 还会因为 `Image.scaledToFit` 的 intrinsic size 影响窗口尺寸。这跟 macOS 原生「相册 App」点开一张图直接铺满屏幕的体验差得很远 —— 看图本身没有沉浸感,标题栏、外部 chrome 都在抢注意力。

## What Changes

- **BREAKING**(行为层) 媒体网格中双击/空格打开预览,不再是主窗口内的 sheet,而是新开一个独立的预览窗口(Photos.app 风格),默认进入 macOS 原生全屏(占满屏幕、自动隐藏菜单栏)
- 预览窗口使用 `.hiddenTitleBar` + 黑色全屏背景;鼠标静止 ~2s 后自动隐藏顶部 header 与底部 metadata,鼠标移动重新淡入(与 macOS 相册/Quick Look 一致)
- ESC 退出全屏并关闭预览窗口(返回媒体库主窗口),Cmd+W 同样关闭;←/→/Space 翻页与关闭逻辑保留
- 关闭预览时同步当前 index 回主窗口的 `selectedIndex`,主窗口选中态与翻页结果一致(行为不变,只是跨窗口而非 sheet-binding)
- `MediaDetailView` 内部固定的 `frame(minWidth: 900, idealWidth: 1100…)` 移除,因为新窗口由全屏 scene 控制尺寸

## Capabilities

### New Capabilities
<!-- 无 -->

### Modified Capabilities
- `media-preview-navigation`: 预览的承载方式从「主窗口内 sheet」变为「独立全屏预览窗口」,同时增加「鼠标静止后 chrome 自动淡出」与「ESC 退出全屏并关闭」两条 requirement;原有的「翻页带方向动画」「缩略图条居中」等不变

## Impact

- 代码:`MyNote/MyNote/MyNoteApp.swift`(新增 `Window` scene + `openWindow`/`dismissWindow` 钩子)、`MyNote/MyNote/MediaLibraryView.swift`(把 `.sheet` 换成 `openWindow`,跨窗口同步选中态)、`MyNote/MyNote/MediaDetailView.swift`(移除固定 frame、加 chrome 自动隐藏、加 ESC 退出全屏)
- 新增轻量数据载体:把当前的 `mediaList + currentIndex` 通过 `@Observable` 或共享 `ObservableObject` 跨窗口传(SwiftUI `Window` scene 不能像 sheet 那样直接 binding)
- 行为:用户从主窗口双击 → 主窗口仍在原位,但屏幕被预览窗占满;关闭预览后焦点回到主窗口、选中态已更新
- 依赖:不引入新 SPM 依赖,仅用 SwiftUI/AppKit
- 不影响:Backend、Vue、Android、Electron;Mac 端写操作策略(只读)、缩略图/大图加载、键盘快捷键映射均保持
