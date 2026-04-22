## Why

Message text 中已经实现了 `#hashtag` 自动解析为 Tag，但 `@actor` 提及没有相应的自动解析。用户希望在 text 中输入 `@xxx` 时自动关联对应的 Actor，与 hashtag 解析保持一致的体验。

## What Changes

- 后端：在消息创建/更新时，从 text 解析 `@actor_name`，自动查找或创建 Actor 并关联到 message.actor_id
- 前端：消息输入框支持 `@` 触发 actor 选择/自动补全（可选，初期可仅依赖文本解析）

## Capabilities

### New Capabilities
- `actor-mention-parse`: 从 message text 中解析 `@xxx` 并自动关联 Actor，包含后端解析逻辑、自动创建 Actor、前端 `@` 高亮显示

### Modified Capabilities
<!-- 无需修改现有 spec -->

## Impact

- `backend/app/services/message_service.py` — 新增 actor 解析函数，类似 `sync_tags_from_text`
- `backend/app/routers/messages.py` — 在 create/update 时调用 actor 解析
- `vue/src/components/MessageCard.vue` — text 渲染时高亮 `@xxx`
- 数据模型不变：复用现有 `Message.actor_id` FK 和 `Actor` 表
- 限制：每条 message 只有一个 actor_id，若 text 中出现多个 `@`，取第一个
