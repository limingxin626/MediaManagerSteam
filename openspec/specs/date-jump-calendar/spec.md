## ADDED Requirements

### Requirement: 点击日期徽章弹出日历
用户 SHALL 能够点击顶部浮动日期徽章，弹出一个日历面板（Popover）。

#### Scenario: 打开日历
- **WHEN** 用户点击顶部浮动日期徽章
- **THEN** 弹出日历面板，显示当前月份，有消息的日期用圆点标记

#### Scenario: 关闭日历
- **WHEN** 用户点击日历外部区域或选择了日期
- **THEN** 日历面板关闭

### Requirement: 日历显示消息分布
日历面板 SHALL 标记有消息的日期，并在切换月份时加载对应月份数据。

#### Scenario: 显示当前月份消息分布
- **WHEN** 日历面板打开
- **THEN** 调用 `/messages/dates` 获取当前月份数据，有消息的日期显示圆点标记

#### Scenario: 切换月份
- **WHEN** 用户在日历中切换到其他月份
- **THEN** 加载该月份的消息分布数据并更新圆点标记；已加载的月份数据 SHALL 被缓存

#### Scenario: 无消息日期不可选
- **WHEN** 日历显示某个日期且该日期无消息
- **THEN** 该日期 SHALL 显示为禁用状态，不可点击

### Requirement: 选择日期跳转消息
用户选择日期后 SHALL 跳转到该日期的消息位置。

#### Scenario: 跳转到有消息的日期
- **WHEN** 用户在日历中点击一个有消息的日期
- **THEN** 消息列表清空并重新加载，以该日期的消息为起点显示
- **THEN** 进入 `isViewingHistory` 状态，显示「回到最新」按钮
- **THEN** 可向上滚动加载更早消息，向下滚动加载更新消息

### Requirement: 深色模式适配
日历面板 SHALL 适配深色模式主题。

#### Scenario: 深色模式下日历样式
- **WHEN** 应用处于深色模式
- **THEN** 日历面板使用深色背景和浅色文字，与整体 UI 风格一致
