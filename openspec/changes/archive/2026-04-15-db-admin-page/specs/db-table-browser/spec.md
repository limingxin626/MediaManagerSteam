## ADDED Requirements

### Requirement: User can browse any database table
系统 SHALL 提供表浏览器界面，用户可以选择任意数据库表并查看其记录列表。

#### Scenario: User selects a table
- **WHEN** 用户在管理页面中点击某个表名（如 "Message"）
- **THEN** 系统显示该表的分页记录列表，每页展示 20 条记录

#### Scenario: Table shows all columns
- **WHEN** 表记录列表加载完成
- **THEN** 系统为每条记录展示所有字段，长文本字段截断显示（最多 100 字符）

### Requirement: Table browser supports pagination
系统 SHALL 使用游标分页浏览表记录，与项目现有分页模式一致。

#### Scenario: User loads next page
- **WHEN** 用户点击"下一页"按钮且 `has_more` 为 true
- **THEN** 系统加载下一页记录并更新显示

#### Scenario: No more pages
- **WHEN** 当前页为最后一页（`has_more` 为 false）
- **THEN** "下一页"按钮禁用

### Requirement: Table browser supports search
系统 SHALL 在表浏览器中提供搜索功能，按文本字段模糊匹配筛选记录。

#### Scenario: User searches records
- **WHEN** 用户在搜索框中输入关键词并确认
- **THEN** 系统仅显示包含该关键词的记录（匹配 text/name 等文本字段）

#### Scenario: Clear search
- **WHEN** 用户清空搜索框
- **THEN** 系统恢复显示全部记录

### Requirement: User can view record details
系统 SHALL 允许用户点击记录行查看完整详情。

#### Scenario: User clicks a record row
- **WHEN** 用户点击表中的某一行
- **THEN** 系统在右侧抽屉面板中展示该记录的所有字段和完整值

### Requirement: User can edit record fields
系统 SHALL 允许用户在详情面板中编辑记录字段并保存。

#### Scenario: User edits and saves
- **WHEN** 用户在详情面板中修改字段值并点击保存
- **THEN** 系统调用对应的 API 更新记录，成功后显示 toast 通知并刷新列表

#### Scenario: Edit validation fails
- **WHEN** 用户提交了无效数据（如必填字段为空）
- **THEN** 系统在对应字段下显示错误提示，不提交请求

### Requirement: User can delete records
系统 SHALL 允许用户删除记录，且需确认后才执行。

#### Scenario: User deletes a record
- **WHEN** 用户在详情面板中点击删除按钮
- **THEN** 系统弹出确认对话框

#### Scenario: User confirms deletion
- **WHEN** 用户确认删除操作
- **THEN** 系统调用 API 删除该记录，关闭面板，刷新列表，显示成功 toast
