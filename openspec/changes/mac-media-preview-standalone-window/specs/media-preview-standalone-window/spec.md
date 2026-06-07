## ADDED Requirements

### Requirement: In-window page navigation

Mac 端预览 SHALL 以 NavigationStack 页面级切换呈现,不新开 OS 窗口。

#### Scenario: Double-click opens preview in same window
- **WHEN** 用户双击媒体网格中的 cell 或按空格
- **THEN** 系统 SHALL 在同一窗口内将内容切换为预览视图
- **AND** 媒体网格、工具栏、DateScrubber 不再可见(被预览页面替换)

#### Scenario: Preview window title shows current media name
- **WHEN** 预览打开且当前索引指向某媒体项
- **THEN** 窗口标题栏 SHALL 显示该媒体文件名的 basename(不含路径)
- **AND** 当用户翻页到下一项时,标题栏 SHALL 即时更新

#### Scenario: ESC or back button closes preview
- **WHEN** 用户在预览中按 ESC 或点击返回按钮
- **THEN** 预览 SHALL 关闭,回到媒体库
- **AND** 媒体库的 `selectedIndex` SHALL 同步为预览中最后看到的索引

### Requirement: Chrome auto-hide

预览页面的 chrome(header 信息栏 + 底部 metadata) SHALL 在鼠标静止 1.5s 后自动淡出,鼠标移动时重新淡入。

#### Scenario: Mouse idle hides chrome
- **WHEN** 用户停止移动鼠标 1.5 秒
- **THEN** chrome SHALL 淡出(opacity → 0),过渡时长 0.25s
- **AND** 媒体内容保持全屏显示

#### Scenario: Mouse movement shows chrome
- **WHEN** 用户移动鼠标(任意位移)
- **THEN** chrome SHALL 立即淡入(opacity → 1)
- **AND** 1.5s 隐藏倒计时 SHALL 被重新触发

#### Scenario: Navigation resets idle timer
- **WHEN** 用户按 ←/→ 翻页或点击关闭按钮
- **THEN** chrome SHALL 立即显示
- **AND** 1.5s 隐藏倒计时 SHALL 被重新触发

### Requirement: Window title reflects current index

预览期间窗口标题 SHALL 实时反映当前媒体的名称。

#### Scenario: Title updates on page change
- **WHEN** 用户从当前媒体翻到列表中的第 N 项
- **THEN** 窗口标题 SHALL 即时更新为第 N 项的 `filePath` basename
- **AND** 如果 `currentIndex` 超出 `mediaList` 范围,标题 SHALL 显示 "媒体预览"

#### Scenario: Title on open
- **WHEN** 预览首次打开
- **THEN** 窗口标题 SHALL 立即显示双击时那一项的 `filePath` basename