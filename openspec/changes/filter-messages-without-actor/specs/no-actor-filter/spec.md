## ADDED Requirements

### Requirement: 后端支持 actor_id=0 查询无 actor 消息
`/messages/with-detail` 端点在收到 `actor_id=0` 时，SHALL 返回 `actor_id IS NULL` 的消息。

#### Scenario: 传入 actor_id=0
- **WHEN** 请求 `GET /messages/with-detail?actor_id=0`
- **THEN** 返回所有 `actor_id IS NULL` 的消息，按 `created_at DESC` 分页

#### Scenario: 传入正常 actor_id
- **WHEN** 请求 `GET /messages/with-detail?actor_id=5`
- **THEN** 行为不变，返回 `actor_id = 5` 的消息

### Requirement: /actors 端点返回无 actor 消息计数
`GET /actors` 响应 SHALL 包含 `no_actor_count` 字段，值为 `actor_id IS NULL` 的消息数量。

#### Scenario: 获取 actor 列表
- **WHEN** 请求 `GET /actors`
- **THEN** 响应中包含 `no_actor_count` 整数字段，等于数据库中 `actor_id IS NULL` 的 Message 行数

### Requirement: Actor 页面显示「无」选项
Actor 页面的 actor 列表顶部 SHALL 显示一个「无」条目，点击后筛选无 actor 关联的消息。

#### Scenario: 页面加载时显示「无」选项
- **WHEN** Actor 页面加载完成
- **THEN** actor 列表最顶部显示「无」条目，右侧显示无 actor 消息的数量

#### Scenario: 点击「无」选项
- **WHEN** 用户点击「无」条目
- **THEN** 右侧消息区域显示所有未关联 actor 的消息
