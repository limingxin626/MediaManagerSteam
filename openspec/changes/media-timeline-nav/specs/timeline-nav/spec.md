## ADDED Requirements

### Requirement: 媒体时间轴数据接口
系统 SHALL 提供 `GET /media/timeline` 接口，返回按月聚合的媒体数量分布。接口 SHALL 接受 `type`（video/image）和 `starred`（boolean）过滤参数，与 `/media` 接口保持一致。返回格式为 `[{year: number, month: number, count: number}]`，按时间降序排列。

#### Scenario: 获取全部媒体的时间分布
- **WHEN** 客户端请求 `GET /media/timeline` 无过滤参数
- **THEN** 返回所有媒体按月聚合的数量分布，按时间降序排列

#### Scenario: 按类型过滤的时间分布
- **WHEN** 客户端请求 `GET /media/timeline?type=video`
- **THEN** 返回仅视频媒体的按月聚合数量分布

#### Scenario: 无媒体数据
- **WHEN** 数据库中无媒体记录
- **THEN** 返回空数组 `[]`

### Requirement: 时间轴导航组件
Media 页面 SHALL 在右侧显示固定的垂直时间轴条。时间轴 SHALL 显示所有有媒体的月份标签（格式：YYYY年M月）。时间轴 SHALL 始终可见且不随页面内容滚动。

#### Scenario: 页面加载后显示时间轴
- **WHEN** Media 页面加载完成
- **THEN** 右侧显示垂直时间轴，包含所有有媒体的月份

#### Scenario: 移动端适配
- **WHEN** 屏幕宽度小于 768px
- **THEN** 时间轴 SHALL 显示为精简模式（仅显示年份和短月份标记）

### Requirement: 时间轴点击跳转
用户点击时间轴上的月份标签时，系统 SHALL 跳转到该月份对应的媒体位置。跳转 SHALL 清空当前 items 并从目标月份的起始时间重新加载。

#### Scenario: 点击跳转到指定月份
- **WHEN** 用户点击时间轴上的"2025年3月"标签
- **THEN** 媒体 grid 清空并从 2025 年 3 月的媒体开始加载显示

#### Scenario: 跳转后继续滚动加载
- **WHEN** 用户跳转到某月份后继续向下滚动
- **THEN** 系统 SHALL 按照正常的 cursor 分页继续加载后续月份的媒体

### Requirement: 滚动位置同步
用户滚动媒体 grid 时，时间轴 SHALL 同步高亮当前可视区域对应的月份。

#### Scenario: 滚动时更新时间轴高亮
- **WHEN** 用户滚动媒体 grid，可视区域顶部的媒体属于 2025 年 1 月
- **THEN** 时间轴上"2025年1月"标签 SHALL 处于高亮状态

#### Scenario: 跨月份滚动
- **WHEN** 用户从 3 月的媒体滚动到 2 月的媒体
- **THEN** 时间轴高亮从"3月"平滑过渡到"2月"

### Requirement: 月份分隔头
媒体 grid 中不同月份的媒体之间 SHALL 插入月份分隔头，显示月份信息。分隔头 SHALL 跨越整行宽度。

#### Scenario: 相邻媒体属于不同月份
- **WHEN** grid 中连续两个媒体分别属于 2025 年 3 月和 2025 年 2 月
- **THEN** 两者之间 SHALL 显示"2025年2月"分隔头

#### Scenario: 同月份媒体不显示分隔头
- **WHEN** grid 中连续两个媒体属于同一月份
- **THEN** 两者之间不显示分隔头

### Requirement: 过滤联动
时间轴数据 SHALL 与媒体过滤条件联动。当用户切换类型过滤或星标过滤时，时间轴 SHALL 重新加载以反映过滤后的时间分布。

#### Scenario: 切换到仅视频过滤
- **WHEN** 用户选择"视频"类型过滤
- **THEN** 时间轴 SHALL 更新为仅显示有视频媒体的月份及对应数量
