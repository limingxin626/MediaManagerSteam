## ADDED Requirements

### Requirement: Mac 端预览以独立全屏窗口承载

在 macOS 客户端 (MyNote/),双击网格 cell 或在选中态按空格触发预览时,系统 SHALL 新开一个独立的预览窗口(不是主窗口内的 sheet),并 SHALL 在窗口出现后立即进入 macOS 原生全屏(menu bar 自动隐藏、占满整个显示器)。

#### Scenario: 双击网格 cell 打开全屏预览
- **WHEN** 用户在 `MediaLibraryView` 网格中双击任意 cell
- **THEN** 系统 SHALL 打开一个独立的预览窗口,并 SHALL 在该窗口可见后立刻进入原生全屏
- **AND** 主窗口 SHALL 保留在原位,不被关闭、不变形

#### Scenario: 空格键打开当前选中项的全屏预览
- **WHEN** 用户在网格聚焦状态下按下空格键且存在 `selectedIndex`
- **THEN** 系统 SHALL 以 `selectedIndex` 为起点新开预览窗口并进入全屏

#### Scenario: 再次双击其他 cell 复用预览窗口
- **WHEN** 预览窗口已经打开,用户回到主窗口双击另一张媒体
- **THEN** 系统 SHALL 复用同一预览窗口(不新开),并 SHALL 把内容切到新选中的媒体并保持全屏

### Requirement: 鼠标静止后 chrome 自动隐藏

预览窗口的顶部信息栏(header)与底部 metadata 区域 SHALL 在鼠标静止超过 1.5 秒后以淡出动画自动隐藏,鼠标重新移动时 SHALL 立刻以淡入动画恢复显示。中间的媒体本体与左右翻页热区 SHALL NOT 受隐藏影响。

#### Scenario: 鼠标静止超过 1.5s
- **WHEN** 鼠标在预览窗口内停止移动超过 1.5 秒
- **THEN** header 与 metadata SHALL 在 ~250ms 内淡出至完全不可见
- **AND** 媒体本体 SHALL 保持显示

#### Scenario: 鼠标重新移动
- **WHEN** chrome 已隐藏,用户移动鼠标(任意距离)
- **THEN** header 与 metadata SHALL 在 ~250ms 内淡入恢复显示
- **AND** 1.5s 静止计时器 SHALL 被重置

#### Scenario: 翻页或按键操作算作活动
- **WHEN** 用户在 chrome 已隐藏时按下 ←/→ 翻页
- **THEN** chrome SHALL 立刻淡入显示,1.5s 静止计时器 SHALL 被重置

### Requirement: ESC / Cmd+W / 空格关闭全屏预览并同步选中态

预览窗口 SHALL 响应 ESC、Cmd+W、空格三种关闭手势,关闭时 SHALL 由系统自动先退出全屏再关闭窗口,主窗口 `MediaLibraryView` 的 `selectedIndex` SHALL 同步为预览中最后看到的那张媒体的索引。

#### Scenario: ESC 关闭预览
- **WHEN** 用户在预览窗口按下 ESC
- **THEN** 系统 SHALL 关闭预览窗口
- **AND** 关闭过程 SHALL 包含原生「退出全屏」过渡(由 macOS 自动完成)
- **AND** 主窗口 `selectedIndex` SHALL 等于预览关闭时的 `currentIndex`

#### Scenario: Cmd+W 关闭预览
- **WHEN** 用户在预览窗口按下 Cmd+W
- **THEN** 行为 SHALL 与 ESC 等价

#### Scenario: 空格关闭预览(与网格态空格打开对称)
- **WHEN** 用户在预览窗口按下空格
- **THEN** 系统 SHALL 关闭预览窗口
- **AND** 主窗口 `selectedIndex` SHALL 同步为预览中最后看到的索引

#### Scenario: 关闭后主窗口自动滚动到当前选中项
- **WHEN** 预览关闭后主窗口被前置
- **THEN** 如果新的 `selectedIndex` 对应的 cell 不在主窗口可视范围,主窗口 SHALL 调 `ensureMediaVisible` 把其滚入视野(复用现有逻辑)

### Requirement: 移除 MediaDetailView 的固定尺寸约束

`MediaDetailView` SHALL NOT 在自身代码中设置 `minWidth/idealWidth/minHeight/idealHeight` 等显式 frame 约束。其尺寸 SHALL 完全由承载它的 `Window` scene(全屏时即为整个屏幕)决定。

#### Scenario: 全屏窗口下任意比例的图都铺满屏幕
- **WHEN** 用户在全屏预览窗口中切换不同长宽比的图片
- **THEN** 主预览区 SHALL 按 `scaledToFit` 自适应当前屏幕尺寸
- **AND** 视图自身 SHALL NOT 触发任何 `frame(minWidth:…)` / `idealWidth` 约束

#### Scenario: 非全屏(用户用绿色信号灯退出全屏后)的窗口仍可正常使用
- **WHEN** 用户点击绿色信号灯退出全屏
- **THEN** 预览窗口 SHALL 转为标准浮动窗口(无标题栏,黑色背景),SHALL NOT 自动关闭
- **AND** 翻页 / chrome 自动隐藏行为 SHALL 保持
