## ADDED Requirements

### Requirement: Tag 模型支持 type 字段
Tag 表 SHALL 包含 `type` 字段（VARCHAR(16)），值为 `tag` 或 `entity`，默认值为 `tag`。

#### Scenario: 创建普通标签
- **WHEN** 通过 `#标签名` 语法或 API 创建标签
- **THEN** 创建的 Tag 记录 type 字段 SHALL 为 `tag`

#### Scenario: 创建实体标签
- **WHEN** 通过 `@实体名` 语法或 API 创建实体
- **THEN** 创建的 Tag 记录 type 字段 SHALL 为 `entity`

### Requirement: Tag 模型支持 description 和 avatar_path
Tag 表 SHALL 包含 `description`（TEXT, nullable）和 `avatar_path`（VARCHAR(1024), nullable）字段。

#### Scenario: 实体标签包含头像和描述
- **WHEN** 查询 type=entity 的 Tag
- **THEN** 响应 SHALL 包含 `description`、`avatar_path` 和自动生成的 `avatar_url` 字段

#### Scenario: 普通标签无头像和描述
- **WHEN** 查询 type=tag 的 Tag
- **THEN** `description` 和 `avatar_path` 字段 SHALL 为 null

### Requirement: 移除 Actor 表和 message.actor_id FK
系统 SHALL 移除独立的 Actor 表和 Message 表的 actor_id 外键列。所有原 Actor 数据 SHALL 作为 type=entity 的 Tag 存在。

#### Scenario: Actor 数据迁移
- **WHEN** 执行数据库迁移
- **THEN** 所有 actor 记录 SHALL 被迁移为 type=entity 的 tag 记录，保留 name、description、avatar_path
- **THEN** 所有 message.actor_id 关联 SHALL 转换为 message_tag 关联行

#### Scenario: 名称冲突处理
- **WHEN** actor.name 与已有 tag.name 重名
- **THEN** 系统 SHALL 保留 actor 的 description 和 avatar_path（合并到已有 tag），并将该 tag 的 type 设为 entity
- **THEN** 原 actor 关联的 message 和原 tag 关联的 message SHALL 合并

### Requirement: Tag API 支持 type 过滤
`GET /tags` 端点 SHALL 支持 `type` 查询参数，用于过滤返回的标签类型。

#### Scenario: 查询所有实体
- **WHEN** 请求 `GET /tags?type=entity`
- **THEN** SHALL 仅返回 type=entity 的标签，包含 avatar_url、description、message_count

#### Scenario: 查询所有普通标签
- **WHEN** 请求 `GET /tags?type=tag`
- **THEN** SHALL 仅返回 type=tag 的标签

#### Scenario: 不指定 type 查询
- **WHEN** 请求 `GET /tags`（不带 type 参数）
- **THEN** SHALL 返回所有类型的标签

### Requirement: Tag 详情 API
`GET /tags/{id}` 端点 SHALL 返回标签详情及其关联的消息列表。

#### Scenario: 查询实体标签详情
- **WHEN** 请求 `GET /tags/{id}`，且该 tag 为 entity 类型
- **THEN** SHALL 返回 tag 基本信息（含 avatar_url、description）和关联的消息列表（含 media_count）

#### Scenario: 查询普通标签详情
- **WHEN** 请求 `GET /tags/{id}`，且该 tag 为 tag 类型
- **THEN** SHALL 返回 tag 基本信息和关联的消息列表
