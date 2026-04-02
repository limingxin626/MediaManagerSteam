### 0) 背景约束（务必遵守）
- 客户端与后端 **保持绝对同步**：客户端会把本地实体的 `id` 当作后端主键使用。
- 如果出现数据冲突（例如并发写入、字段不一致、约束冲突等），冲突如何解决由后端自行决定；但接口必须做到：
  - 成功的条目计入 `applied`
  - 失败的条目计入 `failed`，并记录日志（至少包含 entityType/entityId/operation/error）

### 1) 路由与请求/响应
- 路由：`POST /api/sync/apply`
- 请求 JSON（字段名严格按此定义）：
```json
{
  "changes": [
    {
      "entityType": "ACTOR|MEDIA|MESSAGE|TAG",
      "operation": "UPSERT|DELETE",
      "entityId": 123,
      "payload": { "...": "..." }
    }
  ]
}
```
- 说明：
  - `payload` 在 `DELETE` 时允许为 `null`
  - `payload` 在 `UPSERT` 时必须是对象
  - `changes` 可能为空数组（返回 applied=0, failed=0）

- 响应 JSON：
```json
{ "applied": 0, "failed": 0, "message": "optional" }
```

### 2) 行为语义（非常重要）
对每个 change：
- `UPSERT`：
  - 如果该 `id` 在表里存在则更新，否则插入（以 `id` 为主键）。
  - 要求幂等：同一个 UPSERT 重复提交不会产生额外副作用。
- `DELETE`：
  - 如果存在则删除。
  - 如果不存在也算成功（幂等 delete）。

执行顺序：
- **必须按 `changes` 数组顺序依次执行**（保证客户端操作顺序在服务端重放）。

### 3) 校验与限制
- 限制单次 `changes` 数量（建议最多 200）；超过返回 400。
- 校验 `entityType` 只能是 `ACTOR|MEDIA|MESSAGE|TAG`；`operation` 只能是 `UPSERT|DELETE`；不合法返回 400。

### 4) 数据模型映射（按后端实际表结构实现）
请你按以下四类实体做 upsert/delete。字段名如与你项目不同，请在代码里做映射。

#### Actor
- 表：`actors`
- 主键：`id`
- 字段：`id, name, description, avatarPath, createdAt, updatedAt`

#### Media
- 表：`media`
- 主键：`id`
- 字段：
  - `id, remoteMediaUrl, remoteThumbnailUrl, localMediaPath, localThumbnailPath`
  - `isDownloaded, downloadedAt, fileHash (unique, non-null), fileSize (Long), mimeType`
  - `width, height, durationMs (Long, milliseconds), rating (Int 0-5), starred (Boolean)`
  - `viewCount, lastViewedAt, createdAt, updatedAt`

#### Message
- 表：`messages`
- 主键：`id`
- 字段：`id, text, actorId (FK→actors), starred (Boolean), source, createdAt, updatedAt`

#### Tag
- 表：`tags`
- 主键：`id`
- 字段：`id, name (unique), category, color, createdAt, updatedAt`

payload 容错策略：
- `payload` 可能包含多余字段：请忽略未知字段（不要报错）。
- `payload` 可能缺少字段：
  - 更新（upsert 命中已有记录）时：推荐"只更新 payload 提供的字段，其余保持原值"。
  - 插入（记录不存在）时：缺失字段用默认值或允许 null（由你的模型决定）。

### 5) 事务策略（推荐）
- 推荐采用"逐条 apply、逐条捕获异常、不中断整个批次"的策略：
  - 对每条 change 做 try/catch，失败计数 + 记录日志，然后继续下一条。
- 不强制要求全批次原子性（因为离线队列更适合部分成功推进）。

### 6) 实现建议（按不同数据库）
- PostgreSQL：优先用 `INSERT ... ON CONFLICT (id) DO UPDATE` 来实现 UPSERT。
- SQLite：可用 `INSERT OR REPLACE` 或 `ON CONFLICT`。
- MySQL：可用 `INSERT ... ON DUPLICATE KEY UPDATE`。

### 7) 鉴权（可选）
- 如果你的系统需要鉴权：请给该接口加上 JWT/Token 校验。

### 8) 交付物（请按此输出）
请输出：
1) 完整的路由代码（包含请求/响应 schema）
2) `apply_change(change, db)` 的实现（按 entityType 分发到 Actor/Media/Message/Tag）
3) UPSERT/DELETE 的数据库实现（ORM 或原生 SQL）
4) 一个 curl 示例请求
5) 简短说明：幂等性如何保证、事务策略如何选择、失败如何记录

---

## 额外说明（与你当前 Android 客户端实现对齐）
- 客户端会调用：`POST /api/sync/apply`
- 客户端变更项字段名：`entityType`, `operation`, `entityId`, `payload`
- operation：`UPSERT` 或 `DELETE`
- entityType：`ACTOR` / `MEDIA` / `MESSAGE` / `TAG`

你可以在服务端把每个 change 的处理结果记录到日志，便于定位冲突与失败。
