# MediaManager Backend

基于 FastAPI + SQLite 的个人媒体管理系统后端，以时间流（feed）方式管理图片和视频。**唯一真值源**：Web（Vue/PWA）、桌面端（Electron 包装 Vue，Windows + Mac）与 Android 在线调用/双向同步，Mac（MyNote）为已放弃的旧端。

## 技术栈

- Python 3.13+
- FastAPI + Uvicorn（API 服务，端口 8002）
- SQLAlchemy 2.x + SQLite
- Pillow（图片处理）
- FFmpeg / FFprobe（视频处理）
- onnxruntime（CLIP 本地推理，可选）

## 项目结构

```text
backend/
├── api.py                  # 启动入口（uvicorn 0.0.0.0:8002）
├── app/
│   ├── __init__.py         # FastAPI 应用初始化、CORS、静态文件挂载
│   ├── config.py           # 配置（DATA_ROOT、FFmpeg 路径、媒体类型）
│   ├── runtime.py          # 后台服务统一生命周期
│   ├── models/             # SQLAlchemy ORM 模型
│   ├── shared/             # database、schema 基类与事务边界
│   ├── modules/            # 纵向领域包（router/schema/service/query）
│   │   ├── message/  media/  sync/  collection/  person/  tag/
│   │   ├── repository/     # catalog、watcher、materializer 与 folder 逻辑
│   │   ├── smart/          # CLIP 与智能标签
│   │   ├── transaction/    # 账单解析与交易逻辑
│   │   ├── issue/  todo/
│   │   └── system/         # health、admin 与 dashboard
│   └── utils/              # 文件 hash、缩略图、媒体信息工具函数
├── scripts/                # 运维脚本（初始化、账单分类、数据修复…）
├── alembic/                # 数据库迁移
├── tests/
├── .env.example            # 配置模板（复制为 .env）
└── pyproject.toml
```

## 配置

- `DATA_ROOT` **必填**：数据目录，含 SQLite 库、uploads、thumbs、CLIP 模型
- 配置来源优先级：真实环境变量 / `python api.py --data-root <path>` > `backend/.env`（`load_dotenv(override=False)`）
- 所有走 `from app.*` 的入口（api.py / alembic / scripts/*）自动跟随同一份 `.env`
- 一个 instance == 一个 `DATA_ROOT`，各自独立；日常切 instance 只改 `backend/.env` 的 `DATA_ROOT` 一行

```bash
cd backend
cp .env.example .env   # 改 DATA_ROOT
pip install -e .
python api.py
```

访问 `http://localhost:8002/docs` 查看 Swagger 文档。

## 数据模型

```text
Collection(原 Actor) ── (1:N) ── Message
Message ──┬── MessageMedia (position 排序) ── Media (file_hash 去重)
          ├── message_tag ── Tag
          └── MessageFolder (folder-backed 消息与磁盘目录绑定)
Media ── media_tag ── Tag
Media ── media_person ── Person
Media ── media_embedding（CLIP 向量缓存）
SyncLog / RepositoryFolder / RepositoryFile / Todo / Issue / Transaction / TxnCategoryRule / TelegramSyncState / RemoteMediaReference
```

- **Message** — feed 核心单元；tags 通过 `tag_ids` 显式设置，**无 `#hashtag` 自动解析**
- **Media** — 图片/视频，基于 `file_hash`（Blake2b）全局去重；>100MB 用文件大小
- **MessageMedia** — 关联表，记录 `position` 和 `created_at`（媒体流排序依据）
- **Collection** — 原 Actor 重命名而来，`message.collection_id` 外键
- **文件夹消息** — 非空、非根的 repository folder 自动拥有 folder-backed Message（`repository_catalog` + `folder_message_service`），上传走 `POST /messages/{id}/files` 原子写入 PRIMARY folder，再由 scan → materializer → reconcile 自动出现；folder-backed 消息禁止直接增删/排序 media

## API 概览

### 消息（核心 feed）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/messages/with-detail` | 消息流（含媒体/标签），支持 collection / query / media / tag 过滤、`direction=forward` 正向分页及日历跳转 |
| GET | `/messages` | 分页列表（游标） |
| GET | `/messages/dates` | 指定月份有消息的日期及数量（日历组件） |
| GET | `/messages/search` | 全文搜索 |
| GET | `/messages/sync` | 消息同步快照（Android） |
| POST | `/messages` | 创建消息（`tag_ids` 显式打标） |
| POST | `/messages/merge` / `/{id}/split` | 合并 / 拆分消息 |
| POST | `/messages/{id}/files` | 上传文件（原子写入 PRIMARY folder，202 异步） |
| PATCH | `/messages/{id}` | 更新文字、collection、媒体顺序 |
| DELETE | `/messages/{id}` / `/{id}/media/{media_id}` | 删除消息 / 移除媒体 |

### 媒体

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/media` / `/media/feed` | 媒体时间流（复合游标 `created_at|position`） |
| GET | `/media/timeline` | 时间线聚合项 |
| GET | `/media/{id}` | 详情及关联消息 |
| PUT | `/media/{id}/starred` / `/rating` | 收藏 / 评分 |
| POST | `/media/{id}/rotate` / `/replace` | 旋转 / 替换文件 |
| PUT | `/media/{id}/tags` / `/people` | 设置标签 / 人物 |
| GET/POST | `/media/{id}/previews` | 视频预览片段（章节）列表 / 创建 |
| POST | `/media/{id}/previews/screenshot` | 从视频抽帧 |
| POST | `/media/{id}/cover` | 设置封面 |
| DELETE | `/media/{id}` | 删除媒体 |

### Collection / Person / Tag

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/collections` / `/collections/sync` | Collection 列表 / 同步快照 |
| POST/PUT/DELETE | `/collections` / `/collections/{id}` | Collection CRUD |
| GET/POST | `/people` | 人物列表 / 创建 |
| PUT/DELETE | `/people/{id}` | 人物更新 / 删除 |
| GET/POST | `/tags` | 标签列表（含 message_count）/ 创建 |
| PATCH/DELETE | `/tags/{id}` | 标签更新 / 删除 |

### 文件仓库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/repositories` | 仓库列表 |
| GET | `/repositories/{id}` / `/browse` | 仓库详情 / 目录浏览 |
| POST | `/repositories/{id}/scan` | 触发扫描 |
| GET | `/repositories/duplicate-files` | 重复文件列表（游标） |
| DELETE | `/repositories/duplicate-files/{media_id}` | 删除重复文件 |

### 文件系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/files/list` | 列举目录内容 |
| POST | `/files/upload` / `/upload-media` | 上传文件 / 上传媒体（按日期归档 `{DATA_ROOT}/uploads/YYYY/MM/DD/`） |
| POST | `/files/move` | 移动文件/目录 |
| PUT | `/files/rename` | 重命名 |
| POST | `/files/create` | 创建文件/目录 |
| DELETE | `/files/delete` | 删除 |

通用 `/files/*` 接口**不再接受服务器绝对路径**。调用方必须传 `root_id`（data 或 repositories.json 中的 repository id）和根目录内的 POSIX 相对 path。后端拒绝绝对路径、`..`、符号链接逃逸、根目录删除及跨 root 移动。

### 同步（Android）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/sync/changes?since=&since_id=` | 增量拉取（复合游标，超 `SYNC_LOG_RETENTION_DAYS=365` 返回 410） |
| POST | `/api/sync/apply` | Outbox 批量推送，单事务应用，失败整体回滚 |

### 智能查询（CLIP 本地推理）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/smart/status` | 模型可用性 |
| POST | `/smart/tags/suggest` / `/tags/apply` | 给媒体推荐 Top-K tag / 应用 |
| GET | `/smart/similar/{media_id}` | 图搜图 |
| GET | `/smart/search?q=` | 文搜图 |
| POST | `/smart/embeddings/rebuild` | 批量预计算 embedding |

模型文件放 `{DATA_ROOT}/models/clip/`（`visual.onnx` / `textual.onnx` / `tokenizer.json`，推荐从 OpenAI CLIP ViT-B/32 导出），缺失时 `/smart/*` 返回 503。Embedding 缓存于 `media_embedding` 表（float16 BLOB）。

### 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/transactions` | 账单列表（`/summary/monthly`、`/summary/range`、`/months`、`/categories`） |
| PATCH | `/transactions/{id}` | 账单打标 |
| GET/POST | `/todos` + PATCH/DELETE | 待办看板（含 `/todos/{id}/move`） |
| GET/POST | `/issues` + PATCH/DELETE | 问题看板（含 `/issues/{id}/move`） |
| GET | `/api/dashboard/stats` / `/heatmap` | 统计 / 日期热力图 |
| GET | `/admin/stats` / `/sync-logs` | 管理统计 / 同步日志 |
| GET | `/health` | 健康检查 |

## 分页方式

统一**游标翻页**，响应 `{ items, next_cursor, has_more }`：

- 消息（简单 ISO 游标）：游标 = 上一条 `created_at` ISO 字符串；`/messages/with-detail` 支持 `direction=forward` + `cursor` 正向加载（返回 `prev_cursor` / `has_more_before`）和日历跳转
- 媒体（复合游标）：格式 `"{created_at}|{position}"`，两个字段均 DESC，避免同毫秒多条记录丢失

## 脚本（scripts/）

- `init_data_root.py` — 初始化数据目录
- `bills_*.py` — 月度账单分类流程（切月 / 打印待标 / 应用打标 / 注入 DB），真相之源 `scratch/bills_by_month/*.json`
- `telegram_sync.py` — Telegram Saved Messages 拉取
- `backfill_*.py` / `repair_*.py` / `import_*.py` / `rename_tag.py` / `transcode_gif_previews.py` — 数据修复与导入工具
