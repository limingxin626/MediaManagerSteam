## ADDED Requirements

### Requirement: 详情面板操作栏
详情面板 header 区域 SHALL 包含编辑、删除、收藏三个操作按钮，与 MessageCard 的操作功能对齐。

#### Scenario: 点击编辑按钮
- **WHEN** 用户点击详情面板的编辑按钮
- **THEN** 系统打开 MessageComposeDialog 编辑模式，预填当前消息内容

#### Scenario: 点击删除按钮
- **WHEN** 用户点击详情面板的删除按钮
- **THEN** 系统弹出确认提示，确认后删除消息并关闭详情面板，更新列表

#### Scenario: 点击收藏按钮
- **WHEN** 用户点击详情面板的收藏按钮
- **THEN** 切换消息的 starred 状态，按钮样式同步更新

### Requirement: 媒体网格自适应列数
详情面板的媒体网格 SHALL 根据媒体数量自动调整列数：1张显示为大图，2张显示为2列，3张及以上显示为3列。

#### Scenario: 单张媒体显示为大图
- **WHEN** 消息仅包含1张媒体
- **THEN** 媒体以单列大图展示，宽度填满网格区域

#### Scenario: 两张媒体显示为两列
- **WHEN** 消息包含2张媒体
- **THEN** 媒体以2列网格展示

#### Scenario: 三张及以上媒体显示为三列
- **WHEN** 消息包含3张及以上媒体
- **THEN** 媒体以3列网格展示

### Requirement: 日期显示在 header 区域
日期信息 SHALL 显示在详情面板 header 的标题下方，作为副标题，不再在底部显示。

#### Scenario: header 显示日期
- **WHEN** 详情面板打开
- **THEN** header 区域显示"消息详情"标题和日期副标题

### Requirement: 演员信息展示
如果消息关联了演员，详情面板 SHALL 在文本内容下方展示演员头像和名称。

#### Scenario: 有关联演员时展示
- **WHEN** 消息关联了演员
- **THEN** 在文本下方显示演员头像（圆形）和名称

#### Scenario: 无关联演员时不展示
- **WHEN** 消息未关联演员
- **THEN** 不显示演员区域
