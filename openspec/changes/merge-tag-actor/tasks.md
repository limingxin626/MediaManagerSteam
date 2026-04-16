## 1. 数据库迁移

- [ ] 1.1 创建迁移脚本：备份 SQLite 数据库文件
- [ ] 1.2 ALTER TABLE tag 添加 `type`(VARCHAR(16) DEFAULT 'tag')、`description`(TEXT)、`avatar_path`(VARCHAR(1024)) 列
- [ ] 1.3 检测 actor.name 与 tag.name 重名冲突，合并处理
- [ ] 1.4 将 actor 数据迁移到 tag 表（type='entity'，保留 description、avatar_path）
- [ ] 1.5 将 message.actor_id FK 关系转换为 message_tag 关联行
- [ ] 1.6 更新 sync_log 中 entity_type='ACTOR' 为 'TAG'
- [ ] 1.7 重建 message 表去除 actor_id 列（SQLite 不支持 DROP COLUMN）
- [ ] 1.8 DROP TABLE actor
- [ ] 1.9 验证迁移后数据完整性

## 2. 后端模型层

- [ ] 2.1 更新 Tag 模型：添加 type、description、avatar_path 字段
- [ ] 2.2 移除 Actor 模型类
- [ ] 2.3 移除 Message.actor_id 列和 actor relationship
- [ ] 2.4 更新 SyncLog entity_type 注释

## 3. 后端 Service 层

- [ ] 3.1 扩展 `sync_tags_from_text()` 解析 `@entity` 语法，创建 type=entity 的 Tag
- [ ] 3.2 确保全量替换和合并模式同时处理 # 和 @ 解析结果

## 4. 后端 Schema 层

- [ ] 4.1 更新 TagResponse：添加 type、description、avatar_path、avatar_url 字段
- [ ] 4.2 新增 TagDetailResponse：包含关联消息列表（含 media_count）
- [ ] 4.3 移除 actor.py schema 文件（ActorResponse、ActorDetailResponse、ActorSyncResponse）

## 5. 后端路由层

- [ ] 5.1 更新 `GET /tags`：添加 `type` 查询参数过滤，entity 类型返回 avatar_url
- [ ] 5.2 新增 `GET /tags/{id}` 详情端点：返回 tag 信息 + 关联消息列表
- [ ] 5.3 更新 `GET /actors/sync`：内部改查 tag 表（type=entity），保持响应格式兼容
- [ ] 5.4 移除或重定向其他 actor 端点
- [ ] 5.5 更新 router __init__.py 注册

## 6. 前端类型和 API

- [ ] 6.1 更新 `types.ts`：移除 Actor 类型，更新 Tag 类型（添加 type、description、avatar_url）
- [ ] 6.2 更新 Message 类型：移除 actor_id/actor 字段

## 7. 前端页面和组件

- [ ] 7.1 重构 Actor 页面为 Entity 页面（使用 Tag API with type=entity）
- [ ] 7.2 更新路由配置：`/actor` 路由改为使用 Tag 数据
- [ ] 7.3 更新消息展示组件：显示 @ 引用的实体标签
- [ ] 7.4 更新导航栏链接和图标
