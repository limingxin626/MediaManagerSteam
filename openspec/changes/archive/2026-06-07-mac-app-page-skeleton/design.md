## Context

`MyNote/MyNote/ContentView.swift` 当前只有 11 行,直接渲染 `MediaLibraryView` + 工具栏上的「更换数据目录」按钮。整个 Mac app 的「主窗口」概念只包含一个视图,没有多 tab 切换、没有侧边栏。

要做的事很明确:把主窗口改成「`HStack { Sidebar | 内容区 }`」,左侧固定宽度 200pt 左右的导航栏,右侧根据选中 tab 渲染对应页面。本期三个 tab 中两个是空白占位,只把骨架立起来。

`MediaLibraryView` 本身已经成熟(参见 `mac-media-grid-selection` 与 `mac-native-local-db-media-grid` 两个 change),所有现有交互(选中、方向键、空格预览、双击、虚拟化滚动、DateScrubber)都继续工作。本 change 不动媒体页任何代码,只把它从顶层挪到「媒体 tab」分支里渲染。

## Goals / Non-Goals

**Goals:**
- 启动后主窗口是「左侧导航 + 右侧内容」两段式布局
- 左侧导航有三个按钮:主页 / 消息 / 媒体
- 点击导航按钮切换右侧内容,选中状态有视觉高亮
- 「媒体」tab 渲染现有 `MediaLibraryView`,行为与今天完全一致
- 「主页」/「消息」tab 渲染空白占位页(居中显示 tab 名 + 「敬请期待」)
- 「更换数据目录」按钮仍可访问(从 `ContentView` 工具栏移到合适位置,行为不变)
- 侧边栏宽度固定 200pt,内容区占满剩余空间

**Non-Goals:**
- 不做主页/消息页面的实际业务内容 —— 后续 change 单独实现
- 不做键盘快捷键(⌘1/2/3、⌘[ / ⌘])切换 tab
- 不做可隐藏/可折叠侧边栏
- 不做 tab 顺序拖拽 / 重排
- 不做 tab 状态持久化(关闭 app 后下次打开默认回到「媒体」tab)
- 不做侧边栏图标 + 文字之外的其他状态(角标、loading 指示等)
- 不引入 NavigationSplitView —— 显式用 HStack 简单实现,后续若需要可再切

## Decisions

### Decision 1: 用 `HStack` 手写侧边栏,不用 `NavigationSplitView`

**选择**:
```swift
HStack(spacing: 0) {
    SidebarView(selectedTab: $selectedTab)
        .frame(width: 200)
    Divider()
    content(for: selectedTab)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
}
```

**理由**:
- `NavigationSplitView` 在 macOS 上行为复杂:三栏式 + 可折叠 + 详情列,与本需求「固定两栏」不匹配,反而要写很多约束把它限制住
- 简单的 `HStack` 30 行内能写完,行为完全可控
- 未来若要支持多列(如侧边栏里再嵌二级菜单),再升级到 `NavigationSplitView` 也不迟

**取舍**:失去 `NavigationSplitView` 自带的侧边栏 toggle 按钮。本期不做,non-goal 已声明。

### Decision 2: `AppTab` 枚举作为单一真源

**选择**:
```swift
enum AppTab: String, CaseIterable, Identifiable, Hashable {
    case home, messages, media
    var id: String { rawValue }
    var title: String {
        switch self {
        case .home: return "主页"
        case .messages: return "消息"
        case .media: return "媒体"
        }
    }
    var systemImage: String {
        switch self {
        case .home: return "house"
        case .messages: return "bubble.left.and.bubble.right"
        case .media: return "photo.on.rectangle"
        }
    }
}
```

**理由**:
- 枚举保证 exhaustive:新增 tab 时 switch 编译期报错,避免漏处理
- `Identifiable` + `Hashable` 让 `List` / `ForEach` / `@State` 都能直接用
- 把 title/icon 集中放在枚举上,sidebar 渲染只读不写,后续改文案只动一处

### Decision 3: `selectedTab` 放在 `ContentView` 顶层 `@State`,不进 ViewModel

**选择**:`@State private var selectedTab: AppTab = .media`,作为 `ContentView` 的状态。

**理由**:
- tab 切换是纯 UI 状态,跟数据加载无关
- 现有 `MediaLibraryViewModel` 已经是 `@StateObject` 由 `MediaLibraryView` 自己持有,不让 tab 状态污染 ViewModel
- 媒体 tab 切换是销毁/重建 `MediaLibraryView` 还是 keep-alive?见 Decision 4

**取舍**:无持久化(关闭 app 回到 `.media`)—— non-goal 声明。

### Decision 4: tab 切换销毁/重建内容,不用 `keep-alive`

**选择**:右侧内容直接 `switch selectedTab { case .home: HomePlaceholderView() ... }`,每次切换 tab 都新建视图。

**理由**:
- 本期两个 tab 是空白页,新建无开销
- 媒体 tab 重建会丢失虚拟化网格的滚动位置 —— 这是已知 cost
- 用 `if/else` 简单清晰,避免引入 `.id()` 之类的 hint
- 后续真要保留媒体页滚动位置,改成 `@StateObject` 持有 + 显式创建一次即可

**取舍**:首次从「媒体」切到「主页」再切回,媒体网格重新加载(走 `MediaLibraryView` 重建 → `@StateObject` 重建 → 重新从 `MediaRepository.list` 拉首页)。这是 acceptable,因为 MediaSource 本地查询是同步 GRDB read,耗时 < 50ms。

### Decision 5: 选中项高亮用 SwiftUI 标准的 `List` + `selection` binding

**选择**:`SidebarView` 内部用 `List(selection: $selectedTab)` 渲染 tab 列表,选中态由系统自动管理。

**理由**:
- `List` 在 macOS 自带 sidebar 样式(灰底 + 选中蓝条),与 macOS 视觉规范一致
- `selection` binding 是 SwiftUI 原生 API,自动维护高亮 + 键盘焦点
- 不用手写 `Button` + `isSelected` 判断 + 背景色,代码量少一半

**取舍**:`List` 默认带 divider / padding 等修饰,可能跟项目其他视图风格不一致。本期接受系统默认风格,后续若有 design system 要求再调。

### Decision 6: 占位页用 `VStack + Image + Text`,显式标注「敬请期待」

**选择**:
```swift
struct HomePlaceholderView: View {
    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "house")
                .font(.system(size: 64))
                .foregroundColor(.secondary)
            Text("主页")
                .font(.title)
            Text("敬请期待")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
```

**理由**:
- 空白页 + 单一文字容易让用户以为是 bug;加 icon + 「敬请期待」明示「这里将来会有内容」
- SF Symbol 与 `AppTab.systemImage` 一致,视觉关联
- 代码可预测,后续替换业务实现时整体删除即可

### Decision 7: 「更换数据目录」按钮放在 `SidebarView` 底部,脱离 `ContentView` toolbar

**选择**:把 `ContentView` 里现有的 `ToolbarItem(placement: .automatic)` 按钮迁移到 `SidebarView` 最下方(`Spacer()` + 按钮)。

**理由**:
- 主窗口加了 sidebar 之后,工具栏的「更换数据目录」会显得突兀 —— 跟三个 tab 不在一个语义层
- 数据目录切换是「app 级配置」,放进 sidebar 底部更合理(类似 macOS 多数 app 的偏好设置按钮位置)
- 行为完全不变:`DataRootPicker.chooseDirectory` + `LocalDatabase.validate` + 切换流程不动

**取舍**:侧边栏底部会多占一行(约 32pt)。可接受。

## Risks / Trade-offs

- **[Risk] 媒体 tab 重建丢失滚动位置 / 选中项** → Mitigation:本期接受;后续若用户反馈,改为 keep-alive(`@StateObject` 提到 ContentView 层级)
- **[Risk] `List(selection:)` 在 sidebar 风格下视觉跟现有 `MediaLibraryView` 不一致** → Mitigation:第一版用系统默认;后续 design system 统一
- **[Risk] tab 状态不持久化,关闭 app 回到 `.media`** → Mitigation:non-goal 声明;要做只需 `@AppStorage` 一行
- **[Risk] 侧边栏固定 200pt 在超宽屏上看起来窄、在小窗口上又显宽** → Mitigation:本期固定 200pt,后续根据窗口宽度做 adaptive(隐藏 sidebar 等)
- **[Risk] 切到主页/消息再切回媒体时,媒体页要走完整 `MediaRepository.list` 首页查询** → Mitigation:本地 GRDB 查询 < 50ms,实测无感;真要保状态改 keep-alive
- **[Trade-off] 失去 NavigationSplitView 的 sidebar toggle** → 本期明确不做,后续再加

## Migration Plan

**部署**:
- 无数据迁移、无 backend 改动。直接 `⌘R` 跑即可,启动后即可看到新布局

**回退**:
- `git revert` 本 change 的 commit 即可。`MediaLibraryView` 完全没动,行为不变

**与现有端的兼容**:
- 仅 Mac 端 UI 变化,backend / Android / Vue / Electron 零改动
- 数据库 / DATA_ROOT / Settings 全不动
