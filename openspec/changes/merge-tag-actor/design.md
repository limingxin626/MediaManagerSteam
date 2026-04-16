## Context

当前系统用两个独立的数据模型来描述消息的元信息：

- **Tag**（多对多）：通过 `#hashtag` 从消息文本自动解析，只有 `name` 和 `category` 字段
- **Actor**（一对多 FK）：手动关联，有 `name`、`description`、`avatar_path`，有独立的详情页和头像

两个模型结构高度相似，Actor 的一对多限制（每条消息只能关联一个 actor）已经不满足使用需求。

相关代码：

- 模型定义：`backend/app/models/__init__.py` — Tag, Actor, Message, message_tag 关联表
- Tag 解析：`backend/app/services/message_service.py` — `sync_tags_from_text()` 从 `#` 提取
- Actor 路由：`backend/app/routers/actor.py` — 列表、详情、同步
- Tag 路由：`backend/app/routers/tags.py` — 列表查询
- Actor Schema：`backend/app/schemas/actor.py` — avatar_url 自动填充

## Goals / Non-Goals

**Goals:**

- 合并 Tag 和 Actor 为统一的 Tag 模型，通过 `type` 字段区分
- Actor 从一对多改为多对多（复用 `message_tag` 关联表）
- 消息文本支持 `@entity` 语法，自动解析为 `type=entity` 的 Tag
- 保留 Actor 的详情页能力（头像、描述）
- 数据迁移：现有 actor 数据无损迁移到 tag 表

**Non-Goals:**

- 不做 Android 端的同步协议改动（Android 有独立的 Room DB，后续单独处理）
- 不做 Tag 的层级/嵌套结构
- 不做 Actor 头像上传功能的改造（保持原有文件路径约定）

## Decisions

### 1. 合并为单表 vs 保持双表

**选择：单表合并**

Tag 表新增字段：
- `type` VARCHAR(16) DEFAULT `'tag'` — 值为 `tag` 或 `entity`
- `description` TEXT nullable
- `avatar_path` VARCHAR(1024) nullable

理由：两个模型 90% 相同，合并后只有一套 CRUD、一张关联表。普通 tag 的 description/avatar_path 为 null，不影响性能。未来 tag 想升级为 entity 只需改 type。

替代方案：保持双表但都改为多对多 — 增加维护成本，两套路由/schema/service 代码重复。

### 2. 关联表复用

**选择：复用现有 `message_tag` 关联表**

Actor 之前通过 `message.actor_id` FK 关联，合并后统一走 `message_tag`。迁移时将现有 actor-message FK 关系转为 message_tag 行。

### 3. 文本语法

**选择：`#` 用于 tag，`@` 用于 entity**

`sync_tags_from_text()` 扩展为同时解析 `#tag` 和 `@entity`：
- `#xxx` → 查找或创建 `type=tag` 的记录
- `@xxx` → 查找或创建 `type=entity` 的记录

### 4. API 端点策略

**选择：统一到 `/tags` 路由，通过 `type` 参数过滤**

- `GET /tags?type=entity` — 替代原 `GET /actors`
- `GET /tags/{id}` — 替代原 `GET /actors/{id}`，返回详情 + 关联消息
- `GET /actors/sync` — 保留作为 Android 兼容端点，内部查 tag 表

替代方案：保留 `/actors` 路由做代理 — 增加无意义的胶水代码。

### 5. Message 模型清理

**选择：移除 `message.actor_id` FK 列**

迁移完成后 drop column。SQLAlchemy 模型中移除该字段和 relationship。

## Risks / Trade-offs

- **数据迁移风险** → 迁移前自动备份 SQLite 文件；迁移脚本包含事务回滚
- **Actor name 与 Tag name 冲突** → 迁移时检测重名，如有冲突保留 actor 版本（因为有更丰富的数据），将同名 tag 的关联合并到 actor 记录
- **Android 同步兼容** → SyncLog 中 `ACTOR` entity_type 改为 `TAG`，sync 端点暂时保留但查 tag 表
- **前端改动范围较大** → Actor 相关的组件、路由、类型定义都需要更新

## Migration Plan

1. 备份 SQLite 数据库文件
2. ALTER TABLE tag：添加 `type`、`description`、`avatar_path` 列
3. 检测 actor.name 与 tag.name 的冲突，处理重名
4. 将 actor 数据 INSERT INTO tag（type='entity'）
5. 将 message.actor_id 关系转为 message_tag 行
6. 更新 sync_log 中 entity_type='ACTOR' 为 'TAG'
7. DROP COLUMN message.actor_id（SQLite 需要重建表）
8. DROP TABLE actor
9. 验证数据完整性

回滚策略：保留步骤 1 的备份文件即可完全回滚。

## Open Questions

（无）
