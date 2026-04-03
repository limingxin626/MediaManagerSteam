# 待办事项 / STATUS

> 最后更新：2026-04-03

---

## 🔴 必须手动操作（数据库迁移）

### 1. 现有数据库添加唯一约束和复合索引

SQLite 不支持 `ALTER TABLE ADD CONSTRAINT`，需通过重建表来添加。

**需添加的约束/索引：**
- `tag.name` — UNIQUE
- `actor.name` — UNIQUE
- `message_media(message_id, position)` — UNIQUE
- `message_media(created_at, position)` — 复合索引 `ix_mm_created_at_position`

**操作方式（任选其一）：**
- 方案 A：备份数据库后删除旧库，重启后端让 `create_all` 重建空库，再导入数据
- 方案 B：手动执行 SQLite DDL（重命名旧表 → 建新表 → 迁移数据 → 删旧表）
- 方案 C：引入 Alembic 管理迁移（推荐长期方案，见下方 B-12）

---

## 🔴 必须手动操作（数据修复）

### 2. >100MB 大文件重算哈希

之前 >100MB 文件的 `file_hash` 存的是文件大小字符串（如 `"524288000"`），现在改为采样哈希。**现有记录的 hash 与新算法不兼容，会导致重复上传时无法命中去重。**

**操作步骤：**
1. 查询所有 `file_hash` 为纯数字字符串的 Media 记录
2. 对每条记录重新用新算法计算 hash 并更新数据库
3. 检查是否有因旧 hash 相同而错误合并的记录，手动拆分

```sql
-- 查出受影响的记录
SELECT id, file_path, file_hash, file_size
FROM media
WHERE file_hash GLOB '[0-9]*' AND CAST(file_hash AS INTEGER) = file_size;
```

---

## 🟠 高优先级（功能补全）

### 3. sync/changes 复合游标 — Android 客户端适配

后端 `/sync/changes` 新增了 `since_id` 请求参数和 `next_cursor_id` 响应字段。✅ 后端已完成。

**Android 仍需：**
- `RemoteChangesResponse` 添加 `next_cursor_id: Int?` 字段
- `SyncWorker` / `MessageRepository.syncIncremental()` 在翻页时同时传 `since` + `since_id`

### 4. 消息标签合并模式（B-5）✅ 已修复

`sync_tags_from_text()` 新增 `merge` 参数。`sync/apply` 路径调用时传 `merge=True`，保留原有标签仅追加文本新增标签；message router（用户主动编辑）仍使用 `merge=False` 全量替换。

---

## 🟡 中优先级（工程改进）

### 5. 引入 Alembic 迁移管理（B-12）

现在靠 `create_all(checkfirst=True)` 管理 schema，无版本追踪。

**待做：** 初始化 Alembic，将现有 schema 作为 baseline，后续所有 DDL 变更通过迁移脚本管理。

### 6. SyncLog 自动清理（B-14）

90 天保留期只在查询时校验，不自动删除旧数据，长期运行会无限增长。

**待做：** 添加定时任务（APScheduler 或 uvicorn lifespan），每日删除 `timestamp < now - 90d` 的记录。

### 7. BaseService commit 语义统一（B-15）

`BaseService.create()` / `update()` 内部调用 `db.commit()`，与路由层「统一在末尾 commit」的约定冲突。

**待做：** 将 BaseService 改为只做 `db.flush()`，由调用方控制事务边界。

---

## 🟡 中优先级（sync 竞态，暂不紧急）

### 8. Last-write-wins 竞态条件（B-2）

`_upsert_*` 读取 `existing.updated_at` 后判断是否覆盖，两次操作之间无行锁。

**待做（低并发场景暂缓）：** UPDATE WHERE 子句加入版本号校验，或 SQLite 使用 `BEGIN IMMEDIATE`。

---

## 🔵 低优先级

### 9. 缩略图失败记录（B-10）

缩略图生成失败时仅打 log，前端展示 404 图。

**待做：** Media 表加 `has_thumbnail` 字段，或返回统一占位图 URL。

### 10. ffmpeg 环境变量配置

已在启动时打 warning，但生产部署时应通过 `.env` 或系统环境变量设置正确路径：

```
FFMPEG_PATH=<your ffmpeg path>
FFPROBE_PATH=<your ffprobe path>
```
