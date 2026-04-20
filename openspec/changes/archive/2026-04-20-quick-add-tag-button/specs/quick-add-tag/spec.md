## ADDED Requirements

### Requirement: MessageCard 显示快捷添加 Tag 按钮
MessageCard 的 hover 操作栏 SHALL 包含一个「添加 Tag」图标按钮，与编辑、详情等按钮同级显示。

#### Scenario: 鼠标悬停显示按钮
- **WHEN** 用户将鼠标悬停在 MessageCard 上
- **THEN** 操作栏中显示「添加 Tag」按钮（tag 图标）

### Requirement: 点击按钮弹出 Tag 选择弹窗
点击「添加 Tag」按钮 SHALL 弹出 Popover，展示可选的 tag 列表。

#### Scenario: 打开 Tag 选择弹窗
- **WHEN** 用户点击「添加 Tag」按钮
- **THEN** 弹出 Popover 显示所有已有 tag，按使用频率（message_count）降序排列

#### Scenario: 搜索过滤 Tag
- **WHEN** 弹窗打开后用户在搜索框中输入文字
- **THEN** tag 列表实时过滤，只显示名称包含输入文字的 tag

#### Scenario: 已关联 Tag 标记
- **WHEN** 弹窗显示 tag 列表
- **THEN** 当前 message 已关联的 tag SHALL 显示为已添加状态（视觉区分）

### Requirement: 选择 Tag 后自动插入并更新
选择 tag 后 SHALL 将 `#tagname ` 插入到 message text 开头，并调用 API 更新 message。

#### Scenario: 成功添加新 Tag
- **WHEN** 用户点击一个未关联的 tag
- **THEN** 系统将 `#tagname ` 插入到 message text 开头，调用 PATCH `/messages/{id}` 更新 text，更新成功后本地 message 数据刷新，弹窗关闭

#### Scenario: 尝试添加已存在的 Tag
- **WHEN** 用户点击一个已关联的 tag
- **THEN** 不执行插入，显示 toast 提示「该 Tag 已存在」

#### Scenario: 智能插入位置
- **WHEN** message text 开头已有 `#hashtag` 序列
- **THEN** 新 tag 插入在现有 hashtag 序列之后、正文之前
