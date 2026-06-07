## Why

当前 `MediaLibraryView` 双击打开预览时,`MediaDetailView` 以 overlay 形式覆盖在媒体网格之上 ——底层网格、工具栏、侧边栏仍然可见,只是被半透明层遮挡。这种体验与 macOS 相册(Photos.app)风格差距大:预览应该是与主窗口平等的独立窗口,且窗口标题栏应显示当前图片名称。

## What Changes

- 双击/空格打开预览时,在同一窗口内做页面级切换(NavigationStack push),不再以 overlay 覆盖网格
- 窗口标题栏实时显示当前媒体文件名 (`filePath` 的 basename)
- ESC/返回按钮关闭预览,回到媒体库,`selectedIndex` 已同步
- 鼠标静止 ~1.5s 后 chrome(header + metadata)自动淡出,鼠标移动重新淡入
- 移除 `MediaDetailView` 内部 hardcode 的固定 frame约束

## Capabilities

### New Capabilities
- `media-preview-standalone-window`: 预览以 NavigationStack 页面级切换呈现,单窗口,窗口标题栏显示当前文件名,chrome 自动隐藏

### Modified Capabilities
- `media-preview-navigation`: 预览承载方式从「主窗口内 overlay」改为「独立全屏窗口 + chrome 自动隐藏」

## Impact

- 代码:`MyNote/MyNote/MediaLibraryView.swift`(包 NavigationStack、双击 push destination)、`MyNote/MyNote/MediaDetailView.swift`(移除固定 frame、保留 chrome 自动隐藏)、新增 `MediaPreviewDestination.swift`(数据容器)
- 行为:预览期间同一窗口内页面切换,主窗口内容被预览替换;关闭后 pop 回到媒体库,选中态已同步
- 依赖:无新 SPM 依赖,仅用 SwiftUI
- 不影响:Backend、Vue、Android、Electron