## 1. 后端解析逻辑

- [ ] 1.1 在 `message_service.py` 中添加 `sync_actor_from_text(db, message, text)` 函数：正则 `(?<!\S)@([\w\u4e00-\u9fff\u3400-\u4dbf]+)` 提取第一个 actor name，查找或创建 Actor，设置 `message.actor_id`
- [ ] 1.2 在 `routers/messages.py` 的 create 和 update 端点中调用 `sync_actor_from_text`（在 `sync_tags_from_text` 之后）

## 2. 前端高亮

- [ ] 2.1 在 `MessageCard.vue` 的 text 渲染中添加 `@xxx` 高亮，与 `#hashtag` 高亮使用相同样式
