# MediaManager 数据顶层设计架构文档

> 本文档描述整个系统的数据模型、存储结构、接口契约和同步机制，是各客户端和后端的统一参考来源。

---

## 目录

1. [系统全景](#1-系统全景)
2. [核心数据模型](#2-核心数据模型)
   - 2.1 [后端 SQLite 数据库（Source of Truth）](#21-后端-sqlite-数据库source-of-truth)
   - 2.2 [Android Room 数据库（本地副本）](#22-android-room-数据库本地副本)
   - 2.3 [Vue / PWA（无本地持久化）](#23-vue--pwa无本地持久化)
3. [实体字段详解](#3-实体字段详解)
4. [关系与约束](#4-关系与约束)
5. [API 接口设计](#5-api-接口设计)
   - 5.1 [通用约定](#51-通用约定)
   - 5.2 [消息接口](#52-消息接口)
   - 5.3 [媒体接口](#53-媒体接口)
   - 5.4 [演员接口](#54-演员接口)
   - 5.5 [标签接口](#55-标签接口)
   - 5.6 [同步接口](#56-同步接口)
6. [游标分页机制](#6-游标分页机制)
7. [媒体文件存储与去重](#7-媒体文件存储与去重)
8. [同步架构](#8-同步架构)
   - 8.1 [设计原则](#81-设计原则)
   - 8.2 [SyncLog 变更日志](#82-synclog-变更日志)
   - 8.3 [增量拉取流程](#83-增量拉取流程)
   - 8.4 [推送流程（Outbox 模式）](#84-推送流程outbox-模式)
   - 8.5 [SSE 实时通知](#85-sse-实时通知)
   - 8.6 [Android 后台同步](#86-android-后台同步)
   - 8.7 [冲突解决策略](#87-冲突解决策略)
9. [数据流向总览](#9-数据流向总览)
10. [静态资源映射](#10-静态资源映射)
11. [关键业务规则](#11-关键业务规则)

---

## 1. 系统全景

```
┌─────────────────────────────────────────────────────────────────┐
│                         局域网 (LAN)                             │
│                                                                  │
│  ┌──────────────┐   HTTP/SSE    ┌───────────────────────────┐   │
│  │  Vue / PWA   │ ←──────────→ │  FastAPI 后端 :8002        │   │
│  │  (纯在线)    │               │  SQLite (Source of Truth)  │   │
│  └──────────────┘               │                           │   │
│                                 │  /uploads  静态文件       │   │
│  ┌──────────────┐   HTTP/SSE    │  /asktao   数据目录       │   │
│  │  Electron    │ ←──────────→ │                           │   │
│  │  (Vue 包装)  │               └───────────────────────────┘   │
│  └──────────────┘                          ↑                    │
│                                            │ 双向同步            │
│  ┌──────────────┐   HTTP                  │                    │
│  │  Android     │ ←──────────────────────→┘                    │
│  │  Room DB     │   push outbox / pull delta                    │
│  │  (离线优先)  │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

| 客户端 | 数据层 | 离线能力 | 同步方向 |
|--------|--------|----------|----------|
| Vue / PWA | 内存 + SW 缓存（NetworkFirst） | 仅读缓存 | 单向读取（Pull Only） |
| Electron | 内存（Vue 同上） | 无 | 单向读取 |
| Android | Room SQLite 本地库 | 完全离线读写 | 双向（Push + Pull） |
| 后端 | SQLite（唯一真值源） | — | 接受全部写入，响应全部读取 |

---

## 2. 核心数据模型

### 2.1 后端 SQLite 数据库（Source of Truth）

数据库文件：`{ASKTAO_DATA_ROOT}/db_new.sqlite3`

**ER 图**

```
actor
 └─< message (actor_id FK, SET NULL on delete)
       └─< message_media (message_id FK) >─ media
       └─< message_tag   (message_id FK) >─ tag

sync_log  (独立变更追踪表，不与业务表关联)
```

**表清单**

| 表名 | 说明 |
|------|------|
| `actor` | 演员/分类主体 |
| `message` | 内容条目（文本 + 媒体组合） |
| `media` | 去重后的媒体文件记录 |
| `message_media` | 消息↔媒体多对多（含位置排序） |
| `message_tag` | 消息↔标签多对多 |
| `tag` | 标签（从 `#hashtag` 自动提取） |
| `sync_log` | 变更日志（增量同步基础设施） |

### 2.2 Android Room 数据库（本地副本）

数据库名：`media_management_database`，当前版本：**27**，迁移策略：`fallbackToDestructiveMigration`

**表清单**

| 表名 | 对应后端表 | 差异 |
|------|-----------|------|
| `actors` | `actor` | 字段名 camelCase，时间戳为 Unix ms |
| `messages` | `message` | 多 `source` 字段；Boolean starred（非 0/1） |
| `media` | `media` | 多 `remoteMediaUrl`、`remoteThumbnailUrl`、`localMediaPath`、`isDownloaded`；时间单位 ms |
| `message_media` | `message_media` | 复合主键 (messageId, mediaId) |
| `message_tag` | `message_tag` | 复合主键 (messageId, tagId) |
| `tags` | `tag` | 多 `color`、`createdAt`、`updatedAt` |
| `media_tags` | — | Android 扩展，后端暂无对应 |
| `sync_outbox` | — | 离线操作队列，仅客户端使用 |

### 2.3 Vue / PWA（无本地持久化）

- 数据完全来自 API，存于 Vue 响应式状态（`ref` / `reactive`）
- Service Worker（Workbox）对 API 响应做 `NetworkFirst` 缓存（7 天 TTL），仅用于弱网降级展示
- 无写操作缓存——所有变更实时提交后端

---

## 3. 实体字段详解

### Message（消息）

| 字段 | 后端类型 | Android 类型 | 说明 |
|------|---------|-------------|------|
| `id` | Integer PK | Long | 自增主键 |
| `text` | Text nullable | String? | 消息正文，支持 `#hashtag` |
| `actor_id` / `actorId` | Integer FK nullable | Long? | 演员外键，SET NULL on delete |
| `starred` | Integer 0/1 | Boolean | 收藏标记（SQLite 不支持原生 Boolean） |
| `source` | — | String? | Android 扩展字段，标记本地来源 |
| `created_at` / `createdAt` | DateTime UTC | Long (ms) | 创建时间（分页游标基准字段） |
| `updated_at` / `updatedAt` | DateTime UTC | Long (ms) | 更新时间（冲突解决字段） |

### Media（媒体）

| 字段 | 后端类型 | Android 类型 | 说明 |
|------|---------|-------------|------|
| `id` | Integer PK | Long | |
| `file_path` | String(255) | — | 后端绝对路径，Android 用 remoteMediaUrl 替代 |
| `file_hash` | String(128) unique | String unique | Blake2b 哈希（>100MB 用文件大小代替） |
| `file_size` | Integer | Long? | 字节数 |
| `mime_type` | String(100) | String? | `video/mp4`、`image/jpeg` 等 |
| `width` / `height` | Integer | Int? | 像素尺寸 |
| `duration` | Integer (秒) | Long? (ms) | **注意单位差异**：后端为秒，Android 为毫秒 |
| `rating` | Integer 0–10 | Int 0–5 | 评分（后端 0–10，Android 展示 0–5） |
| `starred` | Integer 0/1 | Boolean | 收藏 |
| `view_count` | Integer | Int | 播放/查看次数 |
| `last_viewed_at` | DateTime | Long? (ms) | 最后查看时间 |
| `remoteMediaUrl` | — | String? | Android 专用：后端文件 URL |
| `remoteThumbnailUrl` | — | String? | Android 专用：缩略图 URL |
| `localMediaPath` | — | String? | Android 专用：本地下载路径 |
| `isDownloaded` | — | Boolean | Android 专用：是否已下载到本地 |
| `created_at` / `createdAt` | DateTime UTC | Long (ms) | |
| `updated_at` / `updatedAt` | DateTime UTC | Long (ms) | |

### Actor（演员）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `name` | String(256) indexed | 唯一名称（非数据库约束，逻辑约定） |
| `description` | Text nullable | 描述 |
| `avatar_path` | String(1024) nullable | 后端头像绝对路径 |
| `created_at` / `updated_at` | DateTime UTC | |

### Tag（标签）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `name` | String(256) indexed | 标签名（无 `#` 前缀） |
| `category` | String(128) nullable indexed | 分类 |
| `color` | — | Android 扩展字段 |

### MessageMedia（关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK（后端） | Android 使用复合主键 (messageId, mediaId) |
| `message_id` / `messageId` | Integer FK | |
| `media_id` / `mediaId` | Integer FK | |
| `position` | Integer | 媒体在消息内排列顺序（0 起始） |
| `created_at` / `createdAt` | DateTime / Long | 媒体页复合游标的时间分量 |

### SyncLog（变更日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK autoincrement | 单调递增，与 timestamp 组成复合游标 |
| `entity_type` | String(32) | `MESSAGE` \| `ACTOR` \| `MEDIA` \| `TAG` |
| `entity_id` | Integer | 被变更实体的 id |
| `operation` | String(16) | `UPSERT` \| `DELETE` |
| `timestamp` | DateTime UTC | 变更发生时间 |

索引：`(timestamp, id)` 复合索引（范围查询主索引）、`(entity_type, entity_id)` 索引（去重查询）

### SyncOutboxItem（Android 离线队列）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Long PK autoincrement | |
| `entityType` | String | `ACTOR` \| `MEDIA` \| `MESSAGE` \| `TAG` |
| `operation` | String | `UPSERT` \| `DELETE` |
| `entityId` | Long | |
| `payloadJson` | String? | UPSERT 时为实体 JSON，DELETE 时为 null |
| `status` | String | `PENDING` \| `DONE` \| `FAILED` |
| `attemptCount` | Int | 推送失败重试次数 |
| `lastError` | String? | 最后一次错误信息 |
| `createdAt` / `updatedAt` | Long (ms) | |

---

## 4. 关系与约束

```
actor (1) ──────────────────────── (N) message
                                        │
                        ┌───────────────┤
                        │               │
               message_media (N:M)   message_tag (N:M)
                        │               │
                       (N)             (N)
                      media            tag
```

**外键行为**

| 关系 | 后端行为 | Android 行为 |
|------|---------|-------------|
| `message.actor_id` → `actor.id` | SET NULL on delete | ForeignKey SET_NULL |
| `message_media.message_id` → `message.id` | CASCADE delete（ORM cascade） | 手动删除（DAO） |
| `message_media.media_id` → `media.id` | 无级联（媒体独立存在） | 无级联 |
| `message_tag.message_id` → `message.id` | 手动删除（router 中 execute） | 手动删除（DAO） |

**唯一约束**

- `media.file_hash` — 全局唯一，保证媒体去重
- `tag.name`（逻辑约定，非数据库约束）— 同名 Tag 只有一条记录

---

## 5. API 接口设计

### 5.1 通用约定

- **Base URL**：`http://192.168.31.146:8002`（局域网，无认证）
- **Content-Type**：`application/json`
- **时间格式**：ISO 8601 字符串，UTC（如 `2026-04-03T10:30:00`）
- **分页**：游标分页，响应结构 `{ items, next_cursor, has_more }`
- **错误**：标准 HTTP 状态码 + `{ detail: string }` 响应体
- **URL 字段自动填充**：Pydantic `model_validator` 在响应序列化时自动填充：
  - `thumb_url` → `/asktao/data/thumbs/{id}.webp`
  - `avatar_url` → `/data/actor_cover/{id}.webp`
  - `file_url` → 绝对路径经 `config.to_url_path()` 转换

### 5.2 消息接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/messages` | 简要列表（游标分页，不含媒体详情） |
| `GET` | `/messages/with-detail` | 详情列表（含 media_items + tags，双向游标） |
| `GET` | `/messages/{id}` | 单条消息详情 |
| `POST` | `/messages` | 创建消息 |
| `PATCH` | `/messages/{id}` | 更新消息（文本、actor、媒体顺序、收藏） |
| `DELETE` | `/messages/{id}` | 删除消息（级联删除 MessageMedia） |
| `POST` | `/messages/merge` | 合并多条消息 |
| `GET` | `/messages/dates` | 按年月统计有消息的日期数量 |
| `GET` | `/messages/around/{id}` | 以指定消息为中心双向加载 |
| `GET` | `/messages/sync` | 全量同步（Android 全量拉取，已被增量端点补充替代） |

**POST /messages 请求体**

```json
{
  "text": "今天拍的照片 #风景 #旅行",
  "actor_id": 3,
  "files": ["/absolute/path/to/file.jpg"]
}
```

**GET /messages/with-detail 查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `cursor` | string | ISO 时间游标 |
| `direction` | `"forward"` | 向前（更新的消息）分页 |
| `limit` | int(1–100) | 默认 20 |
| `actor_id` | int | 按演员过滤 |
| `query_text` | string | 文本全文搜索（ilike） |
| `media_id` | int | 过滤含指定媒体的消息 |
| `tag_id` | int | 过滤含指定标签的消息 |
| `starred` | bool | 收藏过滤 |

### 5.3 媒体接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/media` | 媒体网格（复合游标分页） |
| `GET` | `/media/{id}` | 媒体详情（含关联消息列表） |
| `GET` | `/media/around/{id}` | 以指定媒体为中心双向加载 |
| `PUT` | `/media/{id}/starred` | 切换收藏状态 |
| `PUT` | `/media/{id}/rating` | 设置评分 (0–10) |
| `PUT` | `/media/{id}/view` | 增加查看次数 |

**媒体复合游标格式**：`"{created_at_iso}|{position}"`，两字段均 DESC 排序

### 5.4 演员接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/actors` | 演员列表 |
| `GET` | `/actors/{id}` | 演员详情（含消息摘要） |
| `GET` | `/actors/sync` | 全量同步（Android 拉取） |

### 5.5 标签接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/tags` | 标签列表（含消息计数，按消息数降序） |

### 5.6 同步接口

#### GET /sync/changes

增量拉取，基于 SyncLog 变更日志。

**查询参数**

| 参数 | 必填 | 说明 |
|------|------|------|
| `since` | 是 | ISO timestamp，上次同步的 `server_time` |
| `limit` | 否 | 每批数量，默认 500，最大 1000 |

**响应**

```json
{
  "changes": [
    {
      "entity_type": "MESSAGE",
      "entity_id": 42,
      "operation": "UPSERT",
      "timestamp": "2026-04-03T10:30:00",
      "data": { /* 完整实体快照 */ }
    },
    {
      "entity_type": "MEDIA",
      "entity_id": 15,
      "operation": "DELETE",
      "timestamp": "2026-04-03T10:31:00",
      "data": null
    }
  ],
  "next_cursor": "2026-04-03T10:31:00",
  "has_more": false,
  "server_time": "2026-04-03T12:00:00"
}
```

- `since` 缺失 / 超过 90 天保留期 → **HTTP 410**，客户端须执行全量同步
- 同一 `(entity_type, entity_id)` 在窗口内有多条记录时，只返回最新一条（去重）
- `server_time` 是下次调用的 `since` 值

#### POST /api/sync/apply

接收 Android 推送的本地变更。

**请求体**

```json
{
  "changes": [
    {
      "entityType": "MESSAGE",
      "operation": "UPSERT",
      "entityId": 101,
      "payload": {
        "text": "修改后的文本",
        "starred": true,
        "updatedAt": "2026-04-03T09:00:00"
      }
    },
    {
      "entityType": "MESSAGE",
      "operation": "DELETE",
      "entityId": 55,
      "payload": null
    }
  ]
}
```

**响应**

```json
{ "applied": 2, "failed": 0, "message": null }
```

- 单批上限 200 条（Android 端约定）
- 逐条处理，单条失败不中断批次
- DELETE 幂等（目标不存在时静默跳过）
- UPSERT 幂等（不存在则插入，存在则 Last-write-wins by `updatedAt`）

#### GET /sync/events

SSE 实时变更通知流。

```
data: {"type":"connected"}

data: {"entity_type":"*","entity_id":0,"operation":"REFRESH","timestamp":"2026-04-03T10:30:05"}

: ping
```

- 每 30 秒发送心跳注释 `: ping` 保活
- 事件只携带元数据（`entity_type`、`entity_id`、`operation`、`timestamp`），不含完整数据
- 客户端收到事件后调用 `GET /sync/changes` 获取实际内容
- 进程内事件总线（`asyncio.Queue`），无需外部消息队列

---

## 6. 游标分页机制

系统有两种游标形式：

### 简单 ISO 游标（消息时间线）

```
游标值 = created_at.isoformat()
查询条件 = WHERE created_at < cursor ORDER BY created_at DESC
```

- 双向支持：`direction=forward` + `prev_cursor` 用于日历跳转后向前加载
- 响应附带 `has_more_before` 标志

### 复合游标（媒体网格）

```
游标值 = "{created_at}|{position}"
查询条件 = WHERE (created_at < cursor_time)
           OR (created_at = cursor_time AND position < cursor_position)
ORDER BY created_at DESC, position DESC
```

- 消除 `created_at` 相同时的排序歧义
- `MessageMedia.created_at` 和 `position` 作为两个排序维度

### 通用约定

- 均取 `limit + 1` 行检测 `has_more`，返回前 `limit` 条
- `next_cursor = items[-1].created_at.isoformat()` （当 `has_more=true` 时）
- `null` cursor 代表从最新开始

---

## 7. 媒体文件存储与去重

### 目录结构

```
{ASKTAO_DATA_ROOT}/              # 默认 E:/AskTao
├── db_new.sqlite3               # 数据库文件
├── uploads/
│   └── YYYY/MM/DD/              # 按日期自动归档的上传文件
└── data/
    ├── thumbs/
    │   └── {media_id}.webp      # 缩略图（WebP 格式）
    └── actor_cover/
        └── {actor_id}.webp      # 演员头像（WebP 格式）
```

### 去重流程

```
上传文件
   │
   ▼
计算 Blake2b 哈希（文件 > 100MB 用 file_size 作为哈希）
   │
   ├─ 哈希已存在 → 复用已有 Media 记录，仅创建 MessageMedia 关联
   │
   └─ 哈希不存在 → 创建新 Media 记录
                    → 提取媒体信息（ffprobe）：width、height、duration
                    → 生成缩略图（ffmpeg）→ 存为 {media_id}.webp
                    → db.flush() 获取 id → 创建 MessageMedia
```

### 静态文件 URL 映射

| 系统路径前缀 | URL 路径前缀 |
|------------|------------|
| `E:/AskTao/` | `/asktao/` |
| `F:/AV/` | `/av/` |
| `./uploads/` | `/uploads/` |

`config.to_url_path(absolute_path)` 方法负责路径转换。

---

## 8. 同步架构

### 8.1 设计原则

- **后端是唯一真值源（Source of Truth）**：所有写操作最终必须同步到后端
- **Android 离线优先**：本地写操作先落地 Room 数据库，联网后通过 Outbox 推送
- **SyncLog 追踪删除**：为避免修改现有查询（软删除代价高），用独立的 `sync_log` 表记录包括删除在内的所有变更
- **增量优先，全量兜底**：`GET /sync/changes` 常规路径；服务器返回 `410` 时回退到全量同步
- **无冲突设计**：单用户单局域网，Last-write-wins by `updated_at` 足够

### 8.2 SyncLog 变更日志

**写入时机**：SQLAlchemy `after_flush` 事件监听器在每次 Session flush 时触发，与业务数据在**同一事务**中原子写入。

**监听范围**：`Message`、`Actor`、`Media`、`Tag` 四个模型的 INSERT / UPDATE / DELETE。

**防递归机制**：使用 `threading.local` 标记，避免写入 SyncLog 本身触发二次 flush。

**保留期**：90 天。超过保留期的 `since` 游标返回 `HTTP 410`。

### 8.3 增量拉取流程

```
Android / Vue
    │
    │  GET /sync/changes?since={last_server_time}
    ▼
后端
    ├─ since 缺失 / 超过 90 天 → 返回 410
    │
    └─ 查询 sync_log WHERE timestamp > since
          ORDER BY timestamp ASC, id ASC
          LIMIT 501
       │
       ├─ 去重：同一 (entity_type, entity_id) 取最新记录
       │
       ├─ UPSERT → 附带完整快照（MESSAGE 含嵌套 media_items + tags）
       └─ DELETE → data: null
       │
       └─ 返回 { changes, has_more, server_time }

客户端
    ├─ has_more = true → 递归拉取（用 server_time 作下次 since）
    └─ 完成 → 记录 server_time 到 SharedPreferences
```

### 8.4 推送流程（Outbox 模式）

```
Android 用户操作（创建/修改/删除）
    │
    ▼
写入本地 Room 数据库（立即生效，UI 响应）
    +
写入 sync_outbox 队列（entityType, operation, entityId, payloadJson）

    【联网时（WiFi 恢复 / 定时 WorkManager）】
    │
    ▼
SyncOutboxRepository.syncToServer()
    │
    ├─ 读取 PENDING 条目（最多 200 条）
    ├─ 同 key UPSERT 去重（同一实体的多次 UPSERT 合并为最新一条）
    ├─ DELETE 优先（先清除 pending UPSERT，再入队 DELETE）
    │
    └─ POST /api/sync/apply { changes: [...] }
          │
          ├─ 成功 → 标记 DONE → 删除
          └─ 失败 → 增加 attemptCount，保留队列等待重试
```

**去重规则**（`SyncOutboxRepository`）:

- 同一实体 `enqueueUpsert`：先删除旧的 PENDING UPSERT，再插入新条目
- `enqueueDelete`：先删除所有 PENDING UPSERT 和 DELETE，再插入 DELETE 条目

### 8.5 SSE 实时通知

```
后端 (sync_log_service._after_commit)
    │ 广播到所有订阅队列
    ▼
asyncio.Queue × N（每个 SSE 客户端一个）
    │
    ├─ Vue  →  useSyncEvents composable（EventSource，自动重连）
    │          → 回调驱动，组件按需刷新
    │
    └─ Android  →  SseListener（OkHttp EventSource）
                   → 500ms debounce
                   → 触发 syncIncremental()
```

**Android SseListener 生命周期**：

- 仅在前台 + WiFi 时运行（由 `MainActivity` 通过 `NetworkMonitor` 控制）
- 断线后指数退避重连（2s → 4s → 8s → ... → 30s 上限）

### 8.6 Android 后台同步

由 **WorkManager** 管理，两种任务：

| 任务 | 触发条件 | 工作策略 |
|------|---------|---------|
| 定期同步 | 每 15 分钟（WiFi only） | `KEEP`（保持现有计划） |
| 即时同步 | WiFi 刚连接时 | `REPLACE`（取消旧的，立即执行） |

**SyncWorker 执行流程**（`CoroutineWorker`）：

```
1. Push outbox →  POST /api/sync/apply
2. 读取 SharedPreferences last_sync_time
3. last_sync_time 存在 → syncIncremental(since)
   last_sync_time 不存在 → syncFromRemote()（全量）
4. 结果 NeedFullSync → 执行全量 syncFromRemote()
5. 成功 → 保存新的 server_time 到 SharedPreferences
6. 失败 → Result.retry()（WorkManager 自动退避重试）
```

### 8.7 冲突解决策略

| 场景 | 策略 |
|------|------|
| Android 推送 vs 后端已有更新数据 | `updated_at` 较新者胜（Last-write-wins） |
| Android 离线期间后端已删除该实体 | UPSERT 目标不存在 → 忽略（不重建） |
| Android 推送 DELETE 但后端已无此记录 | 幂等跳过 |
| 两端同时修改同一 Message | 以最后到达后端的 `updated_at` 为准 |

> 单用户单局域网场景下，真正的并发冲突极罕见，此策略足够。

---

## 9. 数据流向总览

### 写入路径

```
Vue / Electron
    └─> POST/PATCH/DELETE API ──> 后端直接写 SQLite
                                      └─> SyncLog 自动记录
                                      └─> SSE 广播通知其他客户端

Android (在线)
    └─> 写 Room + 加入 outbox ──> 联网时 POST /api/sync/apply ──> 后端写 SQLite
                                                                       └─> SyncLog 自动记录

Android (离线)
    └─> 写 Room + 加入 outbox ──> [等待联网] ──> 同上
```

### 读取路径

```
Vue / Electron
    └─> GET API ──> 后端实时查询 SQLite ──> 响应

Android (在线)
    └─> Room 本地查询（Flow/PagingSource，立即响应）
    └─> 后台 SyncWorker 定期同步保持数据新鲜

Android (离线)
    └─> Room 本地查询（完全离线可用）
```

---

## 10. 静态资源映射

| 资源类型 | URL 路径 | 系统路径 |
|---------|---------|---------|
| 媒体文件（AskTao 目录） | `/asktao/{相对路径}` | `E:/AskTao/{相对路径}` |
| 媒体文件（AV 目录） | `/av/{相对路径}` | `F:/AV/{相对路径}` |
| 手机上传文件 | `/uploads/{YYYY/MM/DD/文件名}` | `./uploads/{YYYY/MM/DD/文件名}` |
| 缩略图 | `/asktao/data/thumbs/{id}.webp` | `E:/AskTao/data/thumbs/{id}.webp` |
| 演员头像 | `/asktao/data/actor_cover/{id}.webp` | `E:/AskTao/data/actor_cover/{id}.webp` |

Android 端前缀拼接：`${SyncConfig.BASE_URL} + url_path`，例如：

```
http://192.168.31.146:8002/asktao/data/thumbs/42.webp
```

---

## 11. 关键业务规则

### 标签自动提取

- 消息 `text` 中匹配 `#[\w\u4e00-\u9fff]+` 的内容自动解析为 Tag 记录
- 创建或更新消息时**全量替换**（不是追加），旧 Tag 关联全部清除后重建
- 标签如不存在则自动创建；孤儿 Tag 不自动删除

### 媒体去重

- 文件写入前必须计算 Blake2b 哈希，与 `media.file_hash` 比对
- 哈希已存在 → 复用记录（仅创建 `MessageMedia` 关联），不重复上传文件
- 文件大于 100MB → 使用文件大小（字节数）作为哈希值（当做近似去重）

### 媒体位置排序

- `message_media.position` 从 0 开始，在同一消息内唯一
- 可通过 `PATCH /messages/{id}` 的 `media_order` 字段重新排序
- 前端展示上限为 9 个预览（3×3 宫格），但存储不限数量

### 服务层事务约定

- `media_service.process_file()` 和标签解析调用 `db.flush()`（获取自增 id），**不 commit**
- 路由层负责统一调用 `db.commit()`，保证原子性
- SyncLog 写入与业务数据在同一事务内，commit 后才触发 SSE 广播

### Android starred 字段

- 后端 `message.starred` 是 `Integer(0/1)`，Android 是 `Boolean`
- API 序列化时 Pydantic 自动做 `bool(msg.starred)` 转换
- `PATCH /messages/{id}` 接受 Python `bool`，存储时转回 `1/0`
