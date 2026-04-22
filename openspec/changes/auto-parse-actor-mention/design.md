## Context

现有 `sync_tags_from_text()` 从 message text 解析 `#hashtag` 并同步到 `message.tags`（多对多）。Actor 是单一 FK（`message.actor_id`），每条消息最多一个 actor。需要实现类似的 `@mention` 解析，复用现有 Actor 表和 `UniqueConstraint("name")`。

## Goals / Non-Goals

**Goals:**
- 从 message text 中解析第一个 `@actor_name`，自动查找/创建 Actor 并设置 `message.actor_id`
- 前端渲染时高亮 `@xxx` 文本
- 与 hashtag 解析保持一致的调用时机（create/update）

**Non-Goals:**
- 多 actor 支持（数据模型是单 FK，不改）
- `@` 自动补全/下拉选择（后续迭代）
- Actor 头像自动获取

## Decisions

1. **正则模式**: `@([\w\u4e00-\u9fff\u3400-\u4dbf]+)` — 与 hashtag 正则风格一致，支持中文名
2. **多 `@` 处理**: 取第一个匹配作为 actor，因为 `message.actor_id` 是单值 FK
3. **Actor 自动创建**: 若 name 不存在则 `db.add(Actor(name=name))` + `db.flush()`，与 tag 创建逻辑一致
4. **无 `@` 时不清除**: 如果 text 中没有 `@` 提及，不修改 `actor_id`（避免意外清除手动设置的 actor）
5. **函数命名**: `sync_actor_from_text(db, message, text)` 放在 `message_service.py`

## Risks / Trade-offs

- [名称冲突] Actor name 可能与 hashtag 语法冲突 → 不会，`@` 和 `#` 前缀不同
- [误匹配邮箱] `user@domain.com` 可能误匹配 → 用 `(?<!\S)@` 确保 `@` 前为空白或行首
