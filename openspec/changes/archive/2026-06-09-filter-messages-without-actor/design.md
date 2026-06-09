## Context

Actor 页面采用左右分栏布局：左侧 actor 列表，右侧显示所选 actor 的消息。当前 `actor_id` 为 `NULL` 的消息无法在此页面中被发现。后端 `_build_detail_query` 使用 `if actor_id:` 判断，因此 `actor_id=0` 天然不会匹配任何真实 actor（ID 从 1 开始自增），可作为 "无 actor" 的信号值。

## Goals / Non-Goals

**Goals:**
- 用户可在 Actor 页面查看未关联 actor 的消息
- 保持 API 向后兼容

**Non-Goals:**
- 不修改消息创建/编辑流程
- 不自动将无 actor 消息分配给某个 actor

## Decisions

1. **使用 `actor_id=0` 表示 "无 actor"**
   - 后端 `_build_detail_query` 检测 `actor_id == 0` 时改为 `WHERE actor_id IS NULL`
   - 替代方案：新增独立参数 `no_actor=true`。但这增加 API 表面积，不如复用现有参数简洁

2. **前端在 actor 列表顶部插入虚拟条目**
   - 在 `fetchActors` 返回结果前面插入 `{ id: 0, name: '无', message_count: N }`
   - 计数从后端新增的字段或独立接口获取

3. **后端 `/actors` 返回无 actor 消息计数**
   - 在现有 `/actors` 响应中增加一个独立请求，或在 actor 列表外额外返回
   - 选择方案：前端单独调用 `/messages/count?no_actor=true` 或后端在 `/actors` 响应外包装。最简单的方式是前端用 `actor_id=0` 查一次 `/messages/with-detail?limit=0` 获取 total，但现有接口不返回 total count
   - **决定**：后端 `/actors` 端点额外返回 `no_actor_count` 字段，表示 `actor_id IS NULL` 的消息数量

## Risks / Trade-offs

- [actor_id=0 语义可能令新开发者困惑] → 在路由器代码中添加注释说明
- [如果未来 actor 表允许 id=0] → SQLite autoincrement 从 1 开始，风险极低
