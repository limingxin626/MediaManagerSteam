# MediaManager

个人媒体管理应用，类 Instagram 信息流架构，支持图片和视频的统一管理。设计为局域网自托管使用，无需登录认证（无 auth，仅限可信 LAN）。

## 端 / 客户端

| 端 | 目录 | 状态 | 说明 |
|----|------|------|------|
| 后端 | `backend/` | ✅ 维护中 | FastAPI + SQLAlchemy + SQLite，唯一真值源，端口 8002 |
| **Web / PWA（主要端）** | `vue/` | ✅ 维护中 | Vue 3 + TypeScript + Tailwind v4 |
| **桌面端（主要场景，Windows + Mac）** | `electron/` + `vue/` | ✅ 维护中 | Electron 包装 Vue 前端 |
| **Android（主要端）** | `android/` | ✅ 维护中 | 原生 Kotlin + Jetpack Compose + Room，offline-first 双向同步 |
| Mac（已放弃） | `MyNote/` | 🛑 不再演进 | 原生 SwiftUI + GRDB 直读 SQLite 的旧端 |

## 功能特性

- **消息流** — 类聊天界面的无限滚动 Feed，文本 + 多媒体混合发布，支持合并/拆分
- **媒体管理** — 图片/视频统一管理，基于 Blake2b 哈希自动去重（>100MB 用文件大小做哈希）
- **Collection（原 Actor）** — 按 Collection 分类和筛选消息
- **人物（Person）** — 媒体与人物多对多关联，类似 Mac 相册人物
- **标签系统** — 通过 `tag_ids` 显式设置（创建/更新时），无 `#hashtag` 自动解析
- **收藏** — 消息与媒体均支持 starred（SQLite Integer 0|1）
- **全屏预览** — 图片/视频画廊式浏览，键盘导航、跨消息切换
- **日历导航** — 按日期跳转历史消息；日期热力图（dashboard）
- **搜索** — 消息全文搜索、媒体语义搜索
- **文件仓库** — 把磁盘目录（repository）作为消息的事实来源：folder-backed 消息随文件系统自动出现/清理
- **视频预览/章节** — 从视频抽取帧与片段（`video_media_id` + `frame_ms`/`start_ms`/`end_ms`）
- **智能查询** — CLIP ViT-B/32 本地推理（onnxruntime CPU）：自动打 tag、图搜图、文搜图
- **待办（Todos）** / **问题看板（Issues）** / **账单分类（Transactions）**
- **Telegram 同步** — 从 Telegram "Saved Messages" 拉取媒体（可选）
- **多端同步** — Android ↔ 后端增量双向同步（SyncLog），无冲突合并（单用户模型）
- **多端支持** — Web (PWA)、桌面端（Vue + Electron，Windows + Mac）、Android 为主要场景；Mac 原生端已放弃演进

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy 2.x + SQLite |
| Web | Vue 3 + TypeScript + Tailwind CSS v4（PWA） |
| 桌面端 | Electron 包装 Vue（Windows + Mac 主要场景） |
| Android | Kotlin + Jetpack Compose + Room + Paging3 + Retrofit |
| Mac（旧） | SwiftUI + GRDB（已放弃演进） |
| 媒体处理 | FFmpeg / FFprobe / Pillow |

## 项目结构

```
├── backend/              # FastAPI 后端（唯一真值源）
│   ├── api.py            # 入口，启动 uvicorn (0.0.0.0:8002)
│   ├── app/
│   │   ├── models/       # SQLAlchemy ORM 模型
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   ├── routers/      # API 路由（见下方 API 概览）
│   │   ├── services/     # 业务逻辑（哈希、缩略图、同步日志、仓库目录…）
│   │   ├── utils/        # 工具函数
│   │   └── config.py     # 配置（DATA_ROOT、FFmpeg 路径、媒体类型）
│   ├── scripts/          # 运维脚本（账单分类、初始化、数据修复…）
│   ├── alembic/          # 数据库迁移
│   └── pyproject.toml    # Python 依赖
├── vue/                  # Web / PWA（主要端）
├── android/              # Android 原生端（主要端，Kotlin + Compose + Room）
├── electron/             # 桌面端（Electron 包装 Vue，Windows + Mac 主要场景）
├── MyNote/               # Mac 原生端（SwiftUI + GRDB，已放弃演进）
│   ├── MyNote/           # Swift 源码（PBXFileSystemSynchronizedRootGroup，Xcode 16+）
│   └── MAC_TODO.md       # Xcode 侧设置说明
├── docs/                 # 架构文档、账单分类规则、Telegram 同步说明
├── openspec/             # 开放规范（specs / changes）
└── CLAUDE.md             # 开发指南（最新架构细节以此为准）
```

## 快速开始

### 环境要求

- Python 3.13+
- Node.js 18+ / pnpm（vue，主要端）
- FFmpeg / FFprobe（媒体处理，留空走系统 PATH）
- JDK 17+（Android，主要端）
- Xcode 16+（仅 MyNote 旧端，已放弃演进）

### 后端

```bash
cd backend
cp .env.example .env        # 修改 DATA_ROOT 指向你的数据目录
pip install -e .            # 或: uv pip install -e .
python api.py               # 启动于 0.0.0.0:8002，Swagger: http://localhost:8002/docs
```

**配置来源（优先级 高→低）**：真实环境变量 / `python api.py --data-root <path>` > `backend/.env`。所有走 `from app.*` 的入口（api.py / alembic / scripts/*）自动跟随同一份 `.env`。

一个 instance == 一个 `DATA_ROOT`（各自独立的 db.sqlite3 / uploads / thumbs）；日常切 instance 只改 `backend/.env` 里 `DATA_ROOT` 那行（注释切换）再重启。

### Web 前端（主要端）

```bash
cd vue
pnpm install
pnpm dev                  # 开发服务器 0.0.0.0:5173
pnpm build                # vue-tsc 类型检查 + 生产构建
```

### Android（主要端）

```bash
cd android
./gradlew assembleDebug      # 调试包；assembleRelease 发布包
```

首次使用在 App 内配置后端 baseUrl，走 Outbox 模式离线优先 + 增量同步。

### 桌面端（Electron，Windows + Mac 主要场景；需先启动 Vue dev server）

```bash
cd electron
npm install
npm run dev               # 开发模式（加载 http://localhost:5173）
npm run build             # electron-builder 打包
```

### Mac（MyNote，已放弃演进）

用 Xcode 打开 `MyNote/MyNote.xcodeproj` 可构建运行（GRDB 只读直连 `DATA_ROOT` 下的 SQLite，不依赖后端），但该端已停止演进，仅作参考。Xcode 侧配置见 `MyNote/MAC_TODO.md`。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATA_ROOT` | 数据目录（SQLite 数据库、上传文件、缩略图、CLIP 模型） | 必填，无默认值（在 `backend/.env` 配置） |
| `HOST` | 监听地址 | `0.0.0.0` |
| `PORT` | 监听端口 | `8002` |
| `FFMPEG_PATH` / `FFPROBE_PATH` | ffmpeg/ffprobe 可执行文件路径 | 系统 PATH |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | Telegram Saved Messages 同步（可选） | 空 |

## 数据模型

```
Collection(原 Actor) ── (1:N) ── Message
Message ──┬── MessageMedia (position 排序) ── Media (file_hash 去重)
          ├── message_tag ── Tag
          └── MessageFolder (folder-backed 消息与磁盘目录绑定)
Media ── media_tag ── Tag
Media ── media_person ── Person
Media ── media_embedding（CLIP 向量缓存）
SyncLog（所有业务表变更的增量同步日志）
RepositoryFolder / RepositoryFile（磁盘目录/文件目录，文件系统事实来源）
Todo / Issue / Transaction + TxnCategoryRule / TelegramSyncState + RemoteMediaReference
```

- **游标分页**：消息用简单 ISO 游标（`created_at` ISO 字符串，双向 + 日历跳转）；媒体用复合游标 `"{created_at}|{position}"`（同毫秒多条不丢）。响应统一 `{ items, next_cursor, has_more }`
- **媒体去重**：Blake2b 哈希，>100MB 用文件大小；重复文件自动复用已有 Media
- **缩略图**：WebP 格式，`{DATA_ROOT}/thumbs/{media_id}.webp`
- **上传组织**：按日期归档 `{DATA_ROOT}/uploads/YYYY/MM/DD/`
- **媒体 URL**：后端返回**相对** URL（`file_url` / `thumb_url` / `local_file_path` / `local_thumb_path` 等，见 `MediaUrlMixin`），客户端用自己的 backend baseUrl 拼绝对地址，换网段/主机不产生缓存污染
- **视频预览/章节**：`video_media_id`（自引用父视频）+ `frame_ms` / `start_ms` / `end_ms`，子行表示抽取的帧或章节片段

## 同步（后端 ↔ Android）

单用户 LAN 模型，无 LWW 冲突合并、无 SSE。

- **Pull**：`GET /sync/changes?since=<ISO>&since_id=<int>` — 复合游标 `(timestamp, id)` 增量拉取，同页去重保证 DELETE 覆盖稍晚的 UPSERT；超过 `SYNC_LOG_RETENTION_DAYS=365` 返回 410
- **Push**：`POST /api/sync/apply` — Android Outbox 批量提交，单事务应用，任一失败整体回滚；UPSERT 无条件覆盖

## API 概览

| 路由 | 前缀 | 说明 |
|------|------|------|
| `message.py` | `/messages` | 消息 feed（with-detail / dates / search / merge / split / 上传文件 `POST /messages/{id}/files`） |
| `media.py` | `/media` | 媒体时间流（timeline / feed）、详情、starred / rating / rotate / replace、tags / people、视频 previews、封面 |
| `collection.py` | `/collections` | Collection（原 Actor）CRUD + `/collections/sync` |
| `person.py` | `/people` | 人物 CRUD |
| `tags.py` | `/tags` | 标签 CRUD（含 message_count） |
| `files.py` | `/files` | 文件系统操作：list / upload / upload-media / move / rename / create / delete |
| `sync.py` | `/sync/changes`、`/api/sync/apply` | Android 增量同步 |
| `repositories.py` | `/repositories` | 文件仓库：列表、browse、scan、duplicate-files |
| `smart.py` | `/smart` | CLIP 本地推理：status / tags suggest+apply / similar / search / embeddings rebuild |
| `transactions.py` | `/transactions` | 账单：列表、月度/区间汇总、月份分桶、分类、打标 |
| `todos.py` | `/todos` | 待办看板 |
| `issues.py` | `/issues` | 问题看板 |
| `dashboard.py` | `/api/dashboard` | 统计 stats + 日期 heatmap |
| `admin.py` | `/admin` | stats、sync-logs |
| `health.py` | `/health` | 健康检查 |

完整接口契约见 `docs/ARCHITECTURE.md`；开发细节以 `CLAUDE.md` 为准。

## 账单分类（Transactions）

自动关键词分类已废弃，改走**每月人工（LLM）打标**流程：

- 分类体系（14 类）+ 判断原则 + 月度运行步骤：`docs/bills-categories.md`
- 真相之源：`backend/scratch/bills_by_month/*.json`（已标好的逐月账单，必须保留）
- 脚本：`backend/scripts/bills_*.py`（切月、打印待标、应用打标、注入 DB——先 dry-run 再 `--apply`，apply 前备份 DB）

## 许可证

个人项目，仅供学习参考。
