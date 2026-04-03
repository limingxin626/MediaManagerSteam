# MediaManager 架构文档

> 数据模型、接口契约和同步机制的统一参考。

---

## 1. 系统全景

```
┌─────────────────────────────────────────────────────────────────┐
│                         局域网 (LAN)                             │
│                                                                  │
│  ┌──────────────┐   HTTP/SSE    ┌───────────────────────────┐   │
│  │  Vue / PWA   │ ←──────────→ │  FastAPI 后端 :8002        │   │
│  │  (纯在线)    │               │  SQLite (Source of Truth)  │   │
│  └──────────────┘               └───────────────────────────┘   │
│  ┌──────────────┐   HTTP/SSE               ↑                    │
│  │  Electron    │ ←──────────────────────→ │                    │
│  │  (Vue 包装)  │                           │ 双向同步            │
│  └──────────────┘               ┌───────────────────────────┐   │
│                                 │  Android (Room DB)         │   │
│                                 │  push outbox / pull delta  │   │
│                                 └───────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

| 客户端 | 数据层 | 离线能力 | 同步方向 |
|--------|--------|----------|----------|
| Vue / PWA | 内存 + SW 缓存（NetworkFirst，7 天 TTL） | 仅读缓存 | Pull Only |
| Electron | 内存（同 Vue） | 无 | Pull Only |
| Android | Room SQLite | 完全离线读写 | 双向（Push + Pull） |
| 后端 | SQLite（唯一真值源） | — | 接受全部写入，响应全部读取 |

---

## 2. 数据模型

### ER 图

```
actor (1) ──────────────────────── (N) message
                                        │
                        ┌───────────────┤
                        │               │
               message_media (N:M)   message_tag (N:M)
                        │               │
                       (N)             (N)
                      media            tag

sync_log  （独立变更追踪表，不与业务表关联）
```

### 外键行为

| 关系 | 后端 | Android |
|------|------|---------|
| `message.actor_id` → `actor.id` | SET NULL on delete | ForeignKey SET_NULL |
| `message_media.message_id` → `message.id` | CASCADE（ORM） | 手动删除（DAO） |
| `message_media.media_id` → `media.id` | 无级联 | 无级联 |
| `message_tag.message_id` → `message.id` | 手动删除 | 手动删除（DAO） |

唯一约束：`media.file_hash`（数据库约束）、`tag.name`（逻辑约定）

### Message（消息）

| 字段 | 后端 SQLite | Android Room | Vue / PWA |
|------|-------------|--------------|-----------|
| `id` | Integer PK | Long | number |
| `text` | Text nullable | String? | string \| null |
| `actor_id` | Integer FK nullable | `actorId` Long? | actor_id number \| null |
| `starred` | Integer 0/1 | Boolean | boolean |
| `source` | — | String? | — |
| `created_at` | DateTime UTC | `createdAt` Long (ms) | ISO 字符串 |
| `updated_at` | DateTime UTC | `updatedAt` Long (ms) | ISO 字符串 |

### Media（媒体）

| 字段 | 后端 SQLite | Android Room | Vue / PWA |
|------|-------------|--------------|-----------|
| `id` | Integer PK | Long | number |
| `file_path` | String(255) | — | — |
| `file_hash` | String(128) UNIQUE | String UNIQUE | — |
| `file_size` | Integer | Long? | number |
| `mime_type` | String(100) | String? | string |
| `width` / `height` | Integer | Int? | number |
| `duration` | Integer **秒** ⚠️ | Long? **毫秒** ⚠️ | number (秒) |
| `rating` | Integer **0–10** ⚠️ | Int **0–5** ⚠️ | number (0–10) |
| `starred` | Integer 0/1 | Boolean | boolean |
| `view_count` | Integer | Int | number |
| `last_viewed_at` | DateTime UTC | Long? (ms) | ISO 字符串 |
| `file_url` | 自动填充（Pydantic） | `remoteMediaUrl` String? | file_url |
| `thumb_url` | 自动填充（Pydantic） | `remoteThumbnailUrl` String? | thumb_url |
| `localMediaPath` | — | String? | — |
| `isDownloaded` | — | Boolean | — |
| `created_at` | DateTime UTC | `createdAt` Long (ms) | ISO 字符串 |
| `updated_at` | DateTime UTC | `updatedAt` Long (ms) | ISO 字符串 |

> ⚠️ `duration`：后端秒，Android 毫秒。`rating`：后端 0–10，Android 展示 0–5。

### Actor（演员）

| 字段 | 后端 SQLite | Android Room | Vue / PWA |
|------|-------------|--------------|-----------|
| `id` | Integer PK | Long | number |
| `name` | String(256) indexed | String | string |
| `description` | Text nullable | String? | string \| null |
| `avatar_path` | String(1024) | — | — |
| `avatar_url` | 自动填充（Pydantic） | String? | avatar_url |
| `created_at` | DateTime UTC | `createdAt` Long (ms) | ISO 字符串 |
| `updated_at` | DateTime UTC | `updatedAt` Long (ms) | ISO 字符串 |

### Tag（标签）

| 字段 | 后端 SQLite | Android Room | Vue / PWA |
|------|-------------|--------------|-----------|
| `id` | Integer PK | Long | number |
| `name` | String(256) indexed | String | string |
| `category` | String(128) nullable | String? | string \| null |
| `color` | — | String? | — |
| `created_at` / `updated_at` | — | Long (ms) | — |

### MessageMedia（关联表）

| 字段 | 后端 SQLite | Android Room | Vue / PWA |
|------|-------------|--------------|-----------|
| `id` | Integer PK | — （复合主键） | — |
| `message_id` | Integer FK | `messageId` Long（复合 PK） | 嵌套在消息内 |
| `media_id` | Integer FK | `mediaId` Long（复合 PK） | 嵌套在消息内 |
| `position` | Integer | Int | number |
| `created_at` | DateTime UTC | `createdAt` Long (ms) | ISO 字符串 |

### SyncLog（变更日志，仅后端）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK autoincrement | 单调递增，与 timestamp 组成复合游标 |
| `entity_type` | String(32) | `MESSAGE` \| `ACTOR` \| `MEDIA` \| `TAG` |
| `entity_id` | Integer | 被变更实体的 id |
| `operation` | String(16) | `UPSERT` \| `DELETE` |
| `timestamp` | DateTime UTC | 变更发生时间 |

索引：`(timestamp, id)`（范围查询主索引）、`(entity_type, entity_id)`（去重查询）

### SyncOutboxItem（离线队列，仅 Android）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Long PK autoincrement | |
| `entityType` | String | `ACTOR` \| `MEDIA` \| `MESSAGE` \| `TAG` |
| `operation` | String | `UPSERT` \| `DELETE` |
| `entityId` | Long | |
| `payloadJson` | String? | UPSERT 时为实体 JSON，DELETE 时为 null |
| `status` | String | `PENDING` \| `DONE` \| `FAILED` |
| `attemptCount` | Int | 失败重试次数 |
| `lastError` | String? | 最后一次错误信息 |
| `createdAt` / `updatedAt` | Long (ms) | |

---

## 3. API 接口

**Base URL**：`http://192.168.31.146:8002`（局域网，无认证）
**时间格式**：ISO 8601 UTC。**分页**：游标分页，响应结构 `{ items, next_cursor, has_more }`。
**URL 字段自动填充**（Pydantic `model_validator`）：`thumb_url`、`avatar_url`、`file_url`。

### 消息

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/messages/with-detail` | 详情列表（含 media_items + tags，双向游标） |
| `GET` | `/messages/{id}` | 单条详情 |
| `GET` | `/messages/around/{id}` | 以指定消息为中心双向加载 |
| `GET` | `/messages/dates` | 按年月统计有消息的日期数量 |
| `POST` | `/messages` | 创建（`{ text, actor_id, files: [路径] }`） |
| `PATCH` | `/messages/{id}` | 更新（文本、actor、媒体顺序、收藏） |
| `DELETE` | `/messages/{id}` | 删除（级联删除 MessageMedia） |
| `POST` | `/messages/merge` | 合并多条消息 |

`GET /messages/with-detail` 查询参数：`cursor`、`direction`、`limit`(默认20)、`actor_id`、`query_text`、`media_id`、`tag_id`、`starred`

### 媒体

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/media` | 媒体网格（复合游标分页） |
| `GET` | `/media/{id}` | 详情（含关联消息列表） |
| `GET` | `/media/around/{id}` | 以指定媒体为中心双向加载 |
| `PUT` | `/media/{id}/starred` | 切换收藏 |
| `PUT` | `/media/{id}/rating` | 设置评分 (0–10) |
| `PUT` | `/media/{id}/view` | 增加查看次数 |

### 演员 / 标签

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/actors` | 演员列表 |
| `GET` | `/actors/{id}` | 演员详情（含消息摘要） |
| `GET` | `/actors/sync` | 全量同步（Android 拉取） |
| `GET` | `/tags` | 标签列表（含消息计数，按消息数降序） |

### 同步

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/sync/changes?since={iso}` | 增量拉取；`since` 缺失/超 90 天 → HTTP 410 |
| `POST` | `/api/sync/apply` | 接收 Android 推送（单批上限 200 条） |
| `GET` | `/sync/events` | SSE 实时通知流（每 30 秒 ping 保活） |

`GET /sync/changes` 响应：`{ changes: [{entity_type, entity_id, operation, timestamp, data}], has_more, server_time }`
同一 `(entity_type, entity_id)` 窗口内只返回最新一条；`server_time` 作为下次 `since`。

`POST /api/sync/apply` 请求体：`{ changes: [{entityType, operation, entityId, payload}] }`
响应：`{ applied, failed, message }`。UPSERT/DELETE 均幂等。

SSE 事件只携带元数据，客户端收到后调用 `GET /sync/changes` 获取实际内容。

---

## 4. 游标分页

**简单 ISO 游标**（消息时间线）：`cursor = created_at.isoformat()`，`WHERE created_at < cursor ORDER BY created_at DESC`。支持 `direction=forward` 双向加载。

**复合游标**（媒体网格）：`cursor = "{created_at}|{position}"`，`WHERE (created_at < t) OR (created_at = t AND position < p) ORDER BY created_at DESC, position DESC`。

通用：取 `limit + 1` 行检测 `has_more`；`null` cursor 从最新开始。

---

## 5. 媒体存储与去重

```
{ASKTAO_DATA_ROOT}/          # 默认 E:/AskTao
├── db_new.sqlite3
├── uploads/YYYY/MM/DD/
└── data/
    ├── thumbs/{media_id}.webp
    └── actor_cover/{actor_id}.webp
```

**静态文件 URL 映射**

| 系统路径前缀 | URL 前缀 |
|------------|---------|
| `E:/AskTao/` | `/asktao/` |
| `F:/AV/` | `/av/` |
| `./uploads/` | `/uploads/` |

**去重流程**：计算 Blake2b 哈希（>100MB 用 file_size 代替）→ 哈希已存在则复用 Media 记录，仅创建 MessageMedia 关联；哈希不存在则创建新记录，ffprobe 提取元信息，ffmpeg 生成缩略图。

---

## 6. 同步架构

**设计原则**：后端唯一真值源；Android 离线优先；SyncLog 追踪所有变更（含删除）；增量优先，410 时回退全量；Last-write-wins by `updated_at`。

**SyncLog 写入**：SQLAlchemy `after_flush` 事件，与业务数据同一事务原子写入；`threading.local` 防递归；保留期 90 天。

### 增量拉取

```
客户端 → GET /sync/changes?since={last_server_time}
后端   → 查 sync_log，去重同 entity 多条 → 附完整快照（UPSERT）或 null（DELETE）
客户端 → has_more=true 则递归；完成后保存 server_time
```

### Android 推送（Outbox 模式）

```
用户操作 → 写 Room + 写 sync_outbox（PENDING）
联网时   → 读 PENDING（≤200条），同 key UPSERT 去重，DELETE 优先
         → POST /api/sync/apply → 成功标记 DONE，失败增加 attemptCount
```

### SSE 实时通知

```
后端 after_commit → 广播 asyncio.Queue × N
Vue    → EventSource（自动重连）→ 组件按需刷新
Android → OkHttp EventSource（500ms debounce）→ 触发 syncIncremental()
          仅前台 + WiFi 时运行；断线指数退避重连（上限 30s）
```

### Android 后台同步（WorkManager）

| 任务 | 触发 | 策略 |
|------|------|------|
| 定期同步 | 每 15 分钟（WiFi only） | `KEEP` |
| 即时同步 | WiFi 连接时 | `REPLACE` |

SyncWorker 流程：① Push outbox → ② 有 last_sync_time 则增量，否则全量 → ③ 收到 NeedFullSync 则全量 → ④ 保存 server_time；失败则 `Result.retry()`。

### 冲突解决

| 场景 | 策略 |
|------|------|
| 两端同时修改 | `updated_at` 较新者胜 |
| 推送 UPSERT 但目标已被删除 | 忽略（不重建） |
| 推送 DELETE 但目标不存在 | 幂等跳过 |

---

## 7. 关键业务规则

- **标签提取**：`text` 中 `#[\w\u4e00-\u9fff]+` 自动解析为 Tag；创建/更新时全量替换关联（旧关联清除后重建）；孤儿 Tag 不自动删除。
- **媒体去重**：`media.file_hash` 全局唯一；>100MB 用 file_size 近似去重。
- **媒体排序**：`message_media.position` 从 0 起，同消息内唯一；可通过 `PATCH /messages/{id}` 的 `media_order` 重排；前端展示上限 9 个（3×3），存储不限。
- **事务约定**：`media_service.process_file()` 和标签解析调用 `db.flush()`（获取自增 id），**不 commit**；路由层统一 commit，SyncLog 写入随之完成后触发 SSE 广播。
- **starred 类型**：后端 Integer 0/1，Pydantic 序列化自动转 bool；Android Room 用 Boolean。
