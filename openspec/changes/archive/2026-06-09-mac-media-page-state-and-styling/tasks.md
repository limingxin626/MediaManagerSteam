## 1. tab 切换保留媒体页状态

- [x] 1.1 改 `MyNote/MyNote/ContentView.swift`:把 `private var content: some View` 改为 `ZStack { HomePlaceholderView(); MessagesPlaceholderView(); MediaLibraryView() }`,对每个 view 用 `.opacity(selectedTab == .case ? 1 : 0)` 和 `.allowsHitTesting(selectedTab == .case)` 控制可见性与交互
- [x] 1.2 把 `HStack` 里的 `content` 替换成这个 ZStack(去掉 switch 分支)
- [ ] 1.3 验证:在媒体页滚到中间,选中第 N 张;切到「主页」再切回,网格仍在原位置、选中项仍在第 N 张、桶缓存不重新加载(网络/数据库无新请求)

## 2. 去掉媒体网格蓝色 focus ring

- [x] 2.1 改 `MyNote/MyNote/MediaLibraryView.swift`:`grid` 的 modifier 链 `.focusable(true).focused($gridFocused).onKeyPress { ... }` 末尾追加 `.focusEffectDisabled(true)`
- [ ] 2.2 验证:点击媒体页网格区域,选中项的 `Color.accentColor` 描边正常,但不再有额外的蓝色系统 focus ring 出现
- [ ] 2.3 验证:方向键 / 空格 / ESC 仍然能触发 `handleKeyPress` 内的逻辑(键盘事件没被关闭)

## 3. 去掉媒体网格垂直滚动条

- [x] 3.1 改 `MyNote/MyNote/NSScrollViewBridge.swift`:`makeNSView` 中 `sv.hasVerticalScroller = true` 改为 `sv.hasVerticalScroller = false`
- [x] 3.2 改 `sv.autohidesScrollers = true` 保持不变(对未来再开滚动条时冗余有效),`sv.scrollerStyle = .overlay` 保持不变
- [ ] 3.3 验证:媒体页内容超过一屏时,右侧不再显示滚动条;用滚轮/trackpad 仍能滚动;`DateScrubber` 跳转、方向键移动选中、预览打开/关闭行为均正常
- [ ] 3.4 验证:媒体页内容不足一屏时,无任何滚动相关 UI 出现

## 4. 联调与回归

- [ ] 4.1 启动 app,确认 tab 切换流畅、无报错日志
- [ ] 4.2 完整跑一遍媒体页流程:加载 → 滚动 → 方向键 → 选 bucket → 预览 → 关闭预览 → 切 tab → 切回,确认无视觉/状态异常
- [ ] 4.3 切换「图片/视频/全部」过滤(不走 tab 切换,走媒体页内),确认行为不变(选中重置、加载新桶)
- [ ] 4.4 打开「主页」/「消息」占位页,确认交互正常(点 sidebar 切换可见)、无残影

## 5. 开发日志

- [x] 5.1 在项目根目录的开发日志中追加本次变更(每天一篇日志的规则),记录:Mac 端媒体页修两个 bug —— 切 tab 不再丢滚动/选中状态,网格去掉蓝色 focus ring 和垂直滚动条
