## Why

Actor 页面目前只能选择已有的 actor 来筛选消息，无法查看「没有关联到任何 actor」的消息。这些消息在当前 UI 中完全不可达，用户无法发现和管理它们。

## What Changes

- Actor 页面的 actor 列表顶部增加一个「无」选项，表示筛选 `actor_id IS NULL` 的消息
- 后端 `/messages/with-detail` 和相关接口支持 `actor_id=0` 作为特殊值，表示查询无 actor 关联的消息
- 前端点击「无」时传递 `actor_id=0`，后端将其转换为 `WHERE actor_id IS NULL` 过滤

## Capabilities

### New Capabilities

- `no-actor-filter`: 在 Actor 页面增加「无」选项，支持筛选未关联 actor 的消息

### Modified Capabilities

## Impact

- **后端**: `message.py` 路由器中 `_build_detail_query` 和 `_build_message_query` 需要处理 `actor_id=0` 的特殊语义
- **前端**: `Actor.vue` 需要在 actor 列表顶部插入虚拟的「无」条目，并统计未关联消息数量
- **后端**: `/actors` 端点可能需要额外返回无 actor 消息的计数
