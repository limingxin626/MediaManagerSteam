# MediaManager

个人媒体管理应用，类 Instagram 信息流架构，支持图片和视频的统一管理。设计为局域网自托管使用，无需登录认证。

## 功能特性

- **消息流** — 类聊天界面的无限滚动 Feed，支持文本 + 多媒体混合发布
- **媒体管理** — 图片/视频统一管理，基于 Blake2b 哈希自动去重
- **演员系统** — 按演员分类和筛选内容
- **标签系统** — `#hashtag` 自动解析，消息中的标签自动提取为 Tag 记录
- **全屏预览** — 图片/视频画廊式浏览，支持键盘导航和跨消息切换
- **日历导航** — 按日期快速跳转到历史消息
- **消息合并** — 多选模式下可将多条消息合并为一条
- **搜索与收藏** — 全文搜索、收藏过滤
- **多端支持** — Web (PWA)、桌面 (Electron)、移动端 (Capacitor Android)

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 前端 | Vue 3 + TypeScript + Tailwind CSS v4 |
| 桌面端 | Electron |
| 移动端 | Capacitor (Android) |
| 媒体处理 | FFmpeg / FFprobe / Pillow |

## 项目结构

```
├── backend/              # FastAPI 后端
│   ├── api.py            # 入口，启动 uvicorn (0.0.0.0:8002)
│   ├── app/
│   │   ├── models/       # SQLAlchemy ORM 模型
│   │   ├── schemas/      # Pydantic 请求/响应模型
│   │   ├── routers/      # API 路由 (messages, media, actors, tags, files)
│   │   ├── services/     # 业务逻辑 (文件哈希、缩略图生成、标签解析)
│   │   └── config.py     # 配置
│   └── pyproject.toml    # Python 依赖
├── vue/                  # Vue 3 前端
│   ├── src/
│   │   ├── views/        # 页面 (Message, Media, Actor)
│   │   ├── components/   # 组件 (MessageCard, MediaPreview, CalendarSidebar...)
│   │   ├── composables/  # 组合式函数 (useApi, useToast, useTheme)
│   │   └── types.ts      # TypeScript 类型定义
│   └── package.json
├── electron/             # Electron 桌面端
│   ├── main.js
│   └── package.json
└── CLAUDE.md             # 开发指南
```

## 快速开始

### 环境要求

- Python 3.13+
- Node.js 18+
- pnpm
- FFmpeg / FFprobe（用于视频处理）

### 后端

```bash
cd backend
pip install -e .          # 或: uv pip install -e .
python api.py             # 启动于 0.0.0.0:8002
```

### 前端

```bash
cd vue
pnpm install
pnpm dev                  # 开发服务器 0.0.0.0:5173
pnpm build                # 生产构建
```

### 桌面端 (Electron)

```bash
cd electron
npm install
npm run dev               # 开发模式
npm run build             # 打包分发
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ASKTAO_DATA_ROOT` | 数据目录（SQLite 数据库、上传文件、缩略图） | `E:/AskTao` |
| `FFMPEG_PATH` | ffmpeg 可执行文件路径 | 系统 PATH |
| `FFPROBE_PATH` | ffprobe 可执行文件路径 | 系统 PATH |

## 数据模型

```
Message ──┬── MessageMedia (位置排序) ── Media (按文件哈希去重)
          ├── message_tag ── Tag (自动从 #hashtag 提取)
          └── actor_id ── Actor
```

- **游标分页**：所有列表接口使用 ISO 日期时间字符串作为游标，响应格式 `{ items, next_cursor, has_more }`
- **媒体去重**：文件通过 Blake2b 哈希去重，>100MB 的文件使用文件大小作为哈希
- **缩略图**：存储为 WebP 格式，路径 `{DATA_ROOT}/data/thumbs/{media_id}.webp`
- **上传组织**：按日期自动归档 `{DATA_ROOT}/uploads/YYYY/MM/DD/`

## API 概览

| 路由 | 说明 |
|------|------|
| `GET /messages/with-detail` | 获取消息流 (含媒体、标签) |
| `POST /messages` | 创建消息 |
| `POST /messages/merge` | 合并多条消息 |
| `GET /media` | 媒体网格列表 |
| `GET /actors` | 演员列表 |
| `GET /tags` | 标签列表 |
| `GET /messages/dates` | 按日期统计消息数量 |

## 许可证

个人项目，仅供学习参考。
