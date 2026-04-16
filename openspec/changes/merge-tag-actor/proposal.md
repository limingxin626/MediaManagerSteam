## Why

当前系统中 Tag 和 Actor 是两个独立的数据模型，但它们在结构上高度相似（name unique、多对多关联到 Message）。Actor 目前是一对多 FK（每条消息只能有一个 actor），这限制了使用场景。合并为统一的 Tag 表可以简化数据模型、减少重复代码，同时通过 `type` 字段保留实体级别的丰富度（头像、描述、详情页）。

## What Changes

- **BREAKING**: 移除 `actor` 表，将数据迁移到 `tag` 表
- **BREAKING**: 移除 `message.actor_id` FK，Actor 改为通过 `message_tag` 多对多关联
- Tag 表新增字段：`type`（`tag` | `entity`）、`description`、`avatar_path`
- 消息文本支持 `@entity` 语法引用实体（类似 `#tag`），自动解析为 `type=entity` 的 Tag
- 前端 Actor 页面重构为 Entity 详情页，从统一的 Tag 数据获取
- Actor 相关 API 端点迁移到 Tag 路由下，或作为 Tag 的子集查询

## Capabilities

### New Capabilities
- `unified-tag-model`: 合并 Tag 和 Actor 为统一的 Tag 模型，支持 `type` 字段区分普通标签和实体
- `entity-text-parsing`: 消息文本中 `@entity` 语法的自动解析和关联

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **数据库**: 需要数据迁移脚本，将 actor 数据迁移到 tag 表，更新 message 关联
- **后端 API**: `/actors` 端点需重构或移除，Tag 端点需扩展支持 entity 查询
- **后端 Service**: `message_service.py` 的 hashtag 解析逻辑需扩展支持 `@` 语法
- **前端**: Actor 相关组件（ActorCard、ActorDetail）需改为使用 Tag API
- **类型定义**: `types.ts` 中的 Actor 相关类型需更新
- **Android 同步**: `sync_log` 中的 `ACTOR` entity_type 需要迁移处理
