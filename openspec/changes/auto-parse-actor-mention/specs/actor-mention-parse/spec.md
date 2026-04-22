## ADDED Requirements

### Requirement: 从 message text 解析 @mention 并关联 Actor
系统 SHALL 在消息创建和更新时，从 text 中解析 `@actor_name` 格式的提及，自动查找或创建对应的 Actor，并设置 `message.actor_id`。

#### Scenario: text 包含 @mention 且 actor 已存在
- **WHEN** 用户创建消息，text 为 "这是 @张三 的照片"，且 Actor "张三" 已存在
- **THEN** 系统设置 `message.actor_id` 为已有 Actor "张三" 的 id

#### Scenario: text 包含 @mention 且 actor 不存在
- **WHEN** 用户创建消息，text 为 "这是 @李四 的照片"，且 Actor "李四" 不存在
- **THEN** 系统自动创建 Actor(name="李四") 并设置 `message.actor_id`

#### Scenario: text 包含多个 @mention
- **WHEN** 用户创建消息，text 为 "@张三 和 @李四 的合照"
- **THEN** 系统取第一个 `@张三` 作为 actor 关联

#### Scenario: text 不包含 @mention
- **WHEN** 用户更新消息，新 text 中不包含任何 `@` 提及
- **THEN** 系统不修改 `message.actor_id`（保留原有值）

#### Scenario: 更新消息时更换 @mention
- **WHEN** 用户更新消息，原 actor 为 "张三"，新 text 为 "@李四 的内容"
- **THEN** 系统将 `message.actor_id` 更新为 Actor "李四" 的 id

### Requirement: 前端高亮显示 @mention
系统 SHALL 在消息卡片中将 `@actor_name` 文本以高亮样式渲染，与 `#hashtag` 高亮风格一致。

#### Scenario: 消息文本包含 @mention
- **WHEN** 消息卡片渲染 text "这是 @张三 的照片"
- **THEN** "@张三" 以高亮样式显示，与 `#hashtag` 高亮风格一致
