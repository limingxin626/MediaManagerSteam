# MediaManager Backend

基于 FastAPI + SQLite 的个人媒体管理系统后端，以时间流（feed）方式管理图片和视频。

## 技术栈

- Python 3.13+
- FastAPI + Uvicorn（API 服务，端口 8002）
- SQLAlchemy 2.x + SQLite
- Pillow（图片处理）
- FFmpeg / FFprobe（视频处理）

## 项目结构

```text
backend/
├── api.py                  # 启动入口
├── app/
│   ├── __init__.py         # FastAPI 应用初始化、CORS、静态文件挂载
│   ├── config.py           # 配置（数据目录、FFmpeg 路径、媒体类型）
│   ├── runtime.py         # 后台服务统一生命周期
│   ├── models/
│   │   └── __init__.py     # SQLAlchemy ORM 模型
│   ├── shared/             # database、schema 基类与事务边界
│   ├── modules/            # 纵向领域包（router/schema/service/query）
│   │   ├── message/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── queries.py
│   │   │   └── service.py
│   │   ├── media/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │       ├── queries.py
│   │       └── service.py
│   │   ├── sync/
│   │   ├── collection/、person/、tag/
│   │   ├── repository/   # catalog、watcher、materializer 与 folder 逻辑
│   │   ├── smart/        # CLIP 与智能标签
│   │   ├── transaction/  # 账单解析与交易逻辑
│   │   ├── issue/、todo/
│   │   └── system/        # health、admin 与 dashboard
│   └── utils/
│       └── __init__.py     # 文件 hash、缩略图、媒体信息工具函数
└── db_new.sqlite3          # SQLite 数据库
```

## 数据模型

```text
Message ──── Collection
    │
    ├──── MessageMedia ──── Media
    │
    └──── Tag（多对多，通过 message_tag）
```

- **Message** — feed 核心单元，每条消息对应一个时间点
- **Collection** — 消息合集
- **Media** — 图片/视频资源，基于 `file_hash` 全局去重
- **MessageMedia** — 关联表，记录媒体在消息中的 `position` 和 `created_at`
- **Tag** — 可显式关联到消息或媒体的标签

## 快速启动

```bash
cd backend
pip install -e .
python api.py
```

访问 `http://localhost:8002/docs` 查看 Swagger 文档。

应用通过 `app.create_app()` 创建。集成测试可传入临时 session factory，并用
`start_background_services=False, validate_runtime=False` 隔离真实数据库、静态目录和 watcher。
路由只负责 HTTP 参数与异常映射；完整写用例在领域 service 中统一提交或回滚。

create_app(settings=...) 接受独立的 AppConfig 实例；请求、后台扫描器和媒体处理会绑定到该实例，
因此同一进程内的测试应用不会共享 repository 或 DATA_ROOT 状态。

### 文件 API 路径边界

通用 /files/* 接口不再接受服务器绝对路径。调用方必须传 root_id（data 或
repositories.json 中的 repository id）和根目录内的 POSIX 相对 path。后端拒绝绝对路径、
..、符号链接逃逸、根目录删除及跨 root 移动。/files/upload-media 仍返回可直接提交给
POST /messages 的上传路径，以兼容现有两步上传流程。

## API 概览

## 智能查询（CLIP 本地推理）

`/smart/*` 路由提供基于 CLIP ViT-B/32 的自动打 tag、相似媒体搜索、文本→图片搜索功能，**完全本地推理**（onnxruntime CPU）。

### 模型文件放置

把以下三个文件放到 `{DATA_ROOT}/models/clip/`：

```text
{DATA_ROOT}/models/clip/
├── visual.onnx     # 图像编码器：输入 1x3x224x224 float32，输出 1x512
├── textual.onnx    # 文本编码器：输入 1x77 int64，输出 1x512
└── tokenizer.json  # HuggingFace tokenizers 格式的 CLIP BPE
```

推荐从 HuggingFace 导出 OpenAI CLIP ViT-B/32（`openai/clip-vit-base-patch32`）转 onnx。文件缺失时所有 `/smart/*` 端点返回 503。

### 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/smart/status` | 模型可用性 |
| POST | `/smart/tags/suggest` | 给单个媒体推荐 Top-K tag（按 cosine 排序） |
| POST | `/smart/tags/apply` | 把指定 tag 追加到媒体 |
| GET | `/smart/similar/{media_id}` | 相似媒体列表（图→图） |
| GET | `/smart/search?q=...` | 文本→媒体语义搜索 |
| POST | `/smart/embeddings/rebuild` | 批量预计算（不传 ids 则只补缺失） |

Embedding 缓存到 `media_embedding` 表（float16 BLOB，每条约 1KB）。

## 消息（核心 feed）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/messages` | 分页列表（游标翻页） |
| GET | `/messages/with-detail` | 带媒体详情的列表，支持 `actor_id` / `query_text` / `media_id` / `tag_id` 过滤，支持 `direction=forward` 正向分页及 `inclusive` 日历跳转 |
| GET | `/messages/dates` | 指定月份有消息的日期及数量（供日历组件使用） |
| GET | `/messages/{id}` | 消息详情 |
| POST | `/messages` | 创建消息（批量文件处理，自动解析 `#标签`） |
| PATCH | `/messages/{id}` | 更新消息文字、actor、媒体顺序 |
| DELETE | `/messages/{id}` | 删除消息 |

### 媒体

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/media` | 媒体时间流（基于 `MessageMedia.created_at` 排序） |
| GET | `/media/{id}` | 媒体详情及关联消息 |
| PUT | `/media/{id}/rating` | 更新评分（0–10） |
| PUT | `/media/{id}/view` | 增加浏览次数 |

### 标签

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tags` | 所有标签，附 `message_count`，支持 `name` 模糊搜索 |

### Actor

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/actors` | Actor 列表，支持名称搜索 |
| GET | `/actors/{id}` | Actor 详情及其消息列表 |

### 文件系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/files/list` | 列举目录内容 |
| POST | `/files/upload-media` | 上传媒体文件，返回服务器路径（供手机端使用） |
| POST | `/files/upload` | 上传文件到指定路径（通用） |
| POST | `/files/move` | 移动文件/目录 |
| PUT | `/files/rename` | 重命名 |
| DELETE | `/files/delete` | 删除 |

### 手机端上传流程

```text
POST /files/upload-media   → { "path": "{DATA_ROOT}/uploads/2026/03/26/20260326_143022.jpg" }
POST /messages             → { "files": ["<上一步返回的 path>"], "text": "..." }
```

文件按日期自动落地到 `{DATA_ROOT}/uploads/YYYY/MM/DD/`，文件名为 `YYYYMMDD_HHMMSS.ext`，同秒冲突时追加 `_1`、`_2` 后缀。上传后经过 hash 去重，若与已有媒体重复则自动复用，不创建新的 Media 记录。

## `#标签` 机制

创建或更新消息时，系统自动从 `text` 中提取 `#xxx` 格式的标签：

- 自动创建不存在的 Tag 记录
- 全量替换当前消息的标签关联
- 支持中文标签（如 `#风景` `#旅行`）

## 分页方式

所有列表接口统一使用**游标翻页**（cursor-based pagination）：

- 游标为上一页最后一条记录的 `created_at`（ISO 格式字符串）
- 响应包含 `next_cursor` 和 `has_more` 字段
- `/messages/with-detail` 额外支持：
  - `direction=forward` + `cursor` — 正向加载更新的消息（ASC 排序），返回 `prev_cursor` / `has_more_before`
