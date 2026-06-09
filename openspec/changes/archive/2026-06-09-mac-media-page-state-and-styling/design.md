## Context

`ContentView` 用 `switch selectedTab { case .home: HomePlaceholderView() ... case .media: MediaLibraryView() }` 渲染当前 tab 的 view。SwiftUI 的 view 标识由结构位置决定 —— 同一 `case` 分支在 tab 切换时,旧分支整体从 view 树移除,新分支作为全新 view 树插入。`@StateObject` 的 `wrappedValue` 是惰性初始化的,view 一旦离开层级,`MediaLibraryView` 实例销毁,`StateObject` 持有的 `MediaLibraryViewModel` 也跟着释放。`NSScrollViewBridge` 的 `makeNSView` 创建的 `NSScrollView` 是 view 层的子对象,view 销毁时它也销毁,scrollTop 自然归零。

样式上,SwiftUI 的 `.focusable(true)` 在 macOS 上会触发系统自动绘制的 NSFocusRing —— 默认是蓝色 3pt 描边,跟现有 `MediaGridItem` 选中态用的 `Color.accentColor` 描边是同一类东西但样式不同,叠加起来显得「双层描边」。`NSScrollView` 默认 `hasVerticalScroller = true` 会画出右边的滚动条,跟 Finder 风格不一致。

## Goals / Non-Goals

**Goals:**
- 切到「主页」/「消息」再切回「媒体」,网格保持在原滚动位置、保持原选中项、不重新触发 timeline / 桶加载
- 媒体网格不再有可见的蓝色 focus ring
- 媒体网格不再有可见的垂直滚动条
- 键盘焦点与方向键/空格交互继续正常工作(只是不画 focus ring)
- 程序化跳转/选中项跟随滚动/`ensureMediaVisible` 行为不变

**Non-Goals:**
- 跨重启 app 保留滚动位置 —— 本次只解决同一会话内切 tab 的状态保持
- 主页/消息 tab 之间的状态保持 —— 它们当前是 PlaceholderView,后续接入业务时再做
- 真正完全无 NSScrollView(用 SwiftUI ScrollView 替代) —— 改架构超出本次 bug 修复范围,且 VirtualScrollView 的程序化跳转依赖 NSScrollView 的精确控制
- 多选、拖拽、右键菜单 —— 不在范围
- 改变 `MediaDetailView` 的任何行为

## Decisions

### Decision 1: 用 ZStack 持所有 tab 的 view,通过 opacity 控制可见性

**选择**:
```swift
ZStack {
    HomePlaceholderView()
        .opacity(selectedTab == .home ? 1 : 0)
        .allowsHitTesting(selectedTab == .home)
    MessagesPlaceholderView()
        .opacity(selectedTab == .messages ? 1 : 0)
        .allowsHitTesting(selectedTab == .messages)
    MediaLibraryView()
        .opacity(selectedTab == .media ? 1 : 0)
        .allowsHitTesting(selectedTab == .media)
}
.frame(maxWidth: .infinity, maxHeight: .infinity)
```

**理由**:
- SwiftUI 的 view 树一旦持久化,`@StateObject` 就不会重新创建,这是保留状态最直接的做法
- PlaceholderView 当前没有业务逻辑、没有动画,常驻在层级里几乎没有运行时开销(占位文字/图片)
- 不需要改 `MediaLibraryView` 内部任何代码,只是把它从「被销毁」变成「被隐藏」

**取舍**:
- 三个 view 同时存在会稍微多占一点内存(对 placeholder 而言是 O(1),对媒体页是 view 结构 + ViewModel,不持有加载好的所有 bucket items 之外的额外状态)
- ZStack 会让三个 view 抢同一个坐标系,需要 `.allowsHitTesting` 避免隐藏的 view 拦截点击事件
- 视觉切换不再是默认的 fade —— 切 tab 是「瞬切」(SwiftUI 在 view 树结构不变时不会做过渡动画),这是 macOS sidebar 的标准行为,符合预期

**备选方案否决**:
- `LazyVStack` + `if` 块 + 显式 `.id(selectedTab)`:这等于告诉 SwiftUI「selectedTab 变了,view 完全不同」,状态照样丢
- 用 `TabView` 替代自定义 sidebar:改动大,sidebar 与占位页都要重写,且 `TabView` 在 macOS 上样式与现有 sidebar 风格不一致
- 把 MediaLibraryViewModel 提到 App 级别的 `@StateObject` / `@ObservedObject` + 单例:能解决问题但把 VM 提升到与视图生命周期不一致的位置,后续添加页面或拆分子页时状态归属会乱

### Decision 2: 关掉 focus ring 用 `.focusEffectDisabled(true)`,不替换 focus 机制

**选择**: 在 `grid` 的 `.focusable(true).focused($gridFocused).onKeyPress { ... }` 链上追加 `.focusEffectDisabled(true)`。

**理由**:
- `.focusEffectDisabled(true)`(macOS 14+)只关闭可见的 focus ring 绘制,不改变 view 的焦点能力。`onKeyPress` 仍然能收到事件,方向键/空格/ESC 都正常
- 选中态已有自己的 `RoundedRectangle().stroke(Color.accentColor, lineWidth: 3)` 描边,不需要再叠一层系统 focus ring
- macOS 14+ 已经是项目部署目标(`LocalImageLoader` 用的 webp 原生解码),无新版本门槛

**取舍**:
- 用户用 Tab 键在控件间切换时,看不到「当前焦点在哪」的视觉提示 —— 但媒体网格里有选中描边已经在起这个作用,信息不丢失
- 若未来要在别的 view 上也用 focusable,要记得同样关掉 focus effect;在本 change 里只动媒体网格

### Decision 3: 滚动条直接 `hasVerticalScroller = false`,保留 NSScrollView 实例

**选择**: `NSScrollViewBridge.makeNSView` 里把 `hasVerticalScroller` 改为 `false`,`autohidesScrollers` 改为 `true`(双保险,后者只在 scroller 存在时生效)。

**理由**:
- 用户明确要求「去掉滚动条」,最直接的实现就是关掉它
- NSScrollView 本身的程序化跳转(`clip.scroll(to:)`)、bounds 监听、几何测量仍然需要 —— 不能换成 SwiftUI ScrollView
- 滚动行为(scroll wheel、trackpad inertial、键盘 PgUp/PgDn)不会因为关闭滚动条而失效,macOS NSScrollView 的滚动手势注册在 clip view 上,与 scroller 无关
- 当内容不足一屏时,本来就没有滚动条;现在内容超过一屏时也不显示,符合 Finder/Photos/Music 的视觉

**取舍**:
- 用户失去「滚动条位置 = 当前位置」的视觉指示 —— 媒体页的右侧已经有 `DateScrubber` 标记当前日期,信息不重复
- 失去「拖动滚动条快速跳转」的能力 —— DateScrubber 已经覆盖了按日期跳转,滚动是细粒度的浏览动作,不用滚动条拖拽也合理

### Decision 4: 媒体页 view 始终持焦相关的 onAppear 行为要做幂等处理

**选择**: `MediaLibraryView.onAppear` 里的 `gridFocused = true` 仍然保留。view 不再被销毁/重建,但 `.onAppear` 只在首次出现时调用,后续切回不会重新触发,所以不需要特殊处理。`loadInitial()` 仍只在第一次 `.onAppear` 时被调用 —— 这是想要的行为(避免切回 tab 时重新加载 timeline)。

**理由**:
- 这条决策不是新的「修复」,而是「确认旧行为在新结构下还是正确的」
- `loadInitial` 只跑一次,后续切回 tab 是「显示已有状态」,符合「保持滚动位置」的预期
- 如果发现切回时键盘焦点丢了(因为别的 view 抢了),用户点一下网格区域就能恢复(这是已知行为,跟 mac-media-grid-selection 任务里的取舍一致)

**取舍**: 不引入复杂的焦点管理(`@FocusState` 在多 view 间路由),保持简单。

## Risks / Trade-offs

- **[Risk] ZStack 让三个 view 同时存在,内存占用略增** → Mitigation:Placeholders 几乎零开销,媒体页主要是 ViewModel 持有的桶缓存(图片二进制在 `LocalImageLoader` 的 `NSCache`,不挂在 view 树)。无大图片以 NSImage 形式常驻。
- **[Risk] 切 tab 时不再有淡入淡出动画** → Mitigation:macOS sidebar 标准行为是瞬切,用户对动画无预期。MediaDetailView 内的预览打开/关闭动画(`.transition(.opacity)`)仍正常,因为它是 MediaLibraryView 内部的子 view。
- **[Risk] 媒体页打开时仍然有 NSCache 加载的旧缩略图,可能与「已切换到新数据目录」冲突** → Mitigation:本次不动数据目录切换流程(`changeDataRoot` 仍然 `NSApplication.shared.terminate(nil)` 整个 app,所有 view 自然销毁)。
- **[Risk] `.focusEffectDisabled(true)` 找不到** → Mitigation:这是 macOS 14 API,项目已要求 macOS 14+(webp 原生解码),如编译报缺 API,可在 `MyNote.xcodeproj` 检查 deployment target。
- **[Risk] 关闭滚动条后用户反映失去位置感** → Mitigation:DateScrubber 已经提供位置指示;后续如用户反馈再开回 `autohidesScrollers` 模式。
- **[Risk] 切 tab 后 grid 焦点丢失(因为 SidebarView 的 List 抢走了焦点)** → Mitigation:与 mac-media-grid-selection 任务的已知行为一致(切过滤后焦点丢失),点一下网格即可恢复;本次不引入焦点管理,保持简单。

## Open Questions

无。本次修复目标清晰,没有需要用户决策的分支。
