## Why

Mac app 当前 `ContentView` 只渲染 `MediaLibraryView` 一个视图,功能单一,导航栏缺失。一旦后续要把「主页」(首页仪表盘)、「消息」(message feed)、「媒体」三个模块拆开,需要先把页面骨架搭好,否则后面每加一个 tab 都要在 `ContentView` 里塞 if/else,既乱又难扩展。

需求背景:Mac 是主力端,需要承接 Vue/Android 的「首页 + 信息流 + 媒体库」三段式导航。本期先把骨架立起来——**只做壳子,不做业务**:三个页面占位、左侧栏切换。媒体页保持现有实现;主页/消息页用空白占位(后续单独 change 实现)。

## What Changes

- 新增 **左侧导航栏** `SidebarView`:固定宽度 200pt 左右的列,纵向排列三个按钮(主页 / 消息 / 媒体),当前选中项高亮
- 新增 **内容区**:右侧 `ContentView` 主体,根据当前选中的 tab 渲染对应页面
- 新增 **主页占位页** `HomePlaceholderView`:空白视图 + 居中「主页」文字 + 简短「敬请期待」说明
- 新增 **消息占位页** `MessagesPlaceholderView`:空白视图 + 居中「消息」文字 + 简短「敬请期待」说明
- **保留媒体页** `MediaLibraryView`:代码不动,只挪到内容区的「媒体」tab 分支里渲染
- **改造** `ContentView.swift`:从「直接渲染 `MediaLibraryView`」改为「`HStack { SidebarView + 内容区 }`」,用 `@State selectedTab: AppTab` 跟踪当前 tab
- **新增** `AppTab` 枚举:`home` / `messages` / `media`,作为导航状态类型
- **保留** 工具栏的「更换数据目录」按钮:从 `ContentView` 移到 `SidebarView` 底部或顶层 toolbar,行为不变
- **保留** `OnboardingView` / `Settings` / DATA_ROOT 校验流程:本 change 不触碰启动逻辑

**非目标(明确不做)**:
- 不实现「主页」业务逻辑(仪表盘、统计、最近浏览等) —— 后续 change
- 不实现「消息」业务逻辑(message feed、actor 列表) —— 后续 change
- 不做键盘快捷键切换 tab(⌘1/⌘2/⌘3) —— 后续可选
- 不做可隐藏的侧边栏(用户主动收起) —— 后续可选
- 不改 `MediaLibraryView` / `MediaLibraryViewModel` / `MediaDetailView` 任何代码

## Capabilities

### New Capabilities
- `mac-app-page-skeleton`: Mac app 的主窗口三段式骨架(左侧导航 + 右侧内容),三个 tab 页面占位,媒体页保持现有实现

### Modified Capabilities
<!-- 无。现有 specs 都不涉及 Mac 主窗口的导航/页面切换结构,本期新增独立 capability。 -->

## Impact

- **新增文件**:
  - `MyNote/MyNote/SidebarView.swift` — 左侧导航栏
  - `MyNote/MyNote/HomePlaceholderView.swift` — 主页占位
  - `MyNote/MyNote/MessagesPlaceholderView.swift` — 消息占位
  - `MyNote/MyNote/AppTab.swift` — tab 枚举(可放 SidebarView 同文件,也可独立)
- **修改文件**:
  - `MyNote/MyNote/ContentView.swift` — 改成 HStack 布局 + tab 切换
- **不动**:`MediaLibraryView.swift` / `MediaLibraryViewModel.swift` / `MediaDetailView.swift` / `LocalDatabase.swift` / `Settings.swift` / `OnboardingView.swift` / `MyNoteApp.swift` / `APIClient.swift` / `Models.swift`
- **不影响** backend、Vue、Android、Electron
- **不引入** 新依赖、新 SPM package
