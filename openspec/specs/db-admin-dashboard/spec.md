## ADDED Requirements

### Requirement: Dashboard displays table record counts
系统 SHALL 在管理仪表盘中展示所有数据库表的记录数量，包括 Message、Media、Actor、Tag、MessageMedia、SyncLog。

#### Scenario: User opens dashboard
- **WHEN** 用户访问 `/admin` 页面
- **THEN** 系统显示每个数据库表的名称和对应的记录总数

#### Scenario: Dashboard data refreshes
- **WHEN** 用户点击刷新按钮
- **THEN** 系统重新查询并更新所有表的记录数

### Requirement: Dashboard displays storage statistics
系统 SHALL 显示媒体文件的存储统计信息，包括总文件数、总存储大小。

#### Scenario: Storage stats shown
- **WHEN** 仪表盘加载完成
- **THEN** 系统展示媒体文件总数、总存储大小（格式化为 GB/MB）

### Requirement: Dashboard shows recent activity
系统 SHALL 显示最近创建或更新的记录摘要。

#### Scenario: Recent messages shown
- **WHEN** 仪表盘加载完成
- **THEN** 系统展示最近 5 条 Message 的创建时间和文本摘要
