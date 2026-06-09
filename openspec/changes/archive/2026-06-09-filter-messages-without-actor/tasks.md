## 1. 后端

- [x] 1.1 修改 `_build_detail_query` 和 `_build_message_query`：当 `actor_id == 0` 时过滤 `Message.actor_id IS NULL`
- [x] 1.2 修改 `/actors` 端点，在响应中增加 `no_actor_count` 字段（`actor_id IS NULL` 的消息数量）
- [x] 1.3 更新 Pydantic schema 以包含 `no_actor_count`

## 2. 前端

- [x] 2.1 在 `Actor.vue` 的 actor 列表顶部插入「无」虚拟条目（id=0），显示 `no_actor_count`
- [x] 2.2 点击「无」时以 `actor_id=0` 请求消息列表
- [x] 2.3 更新前端类型定义以匹配后端新增字段
