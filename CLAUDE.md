# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal media management app with an Instagram-like feed architecture. Self-hosted on LAN. The project is in Chinese (comments, docs, UI strings).

## Architecture

- **Backend**: FastAPI + SQLAlchemy + SQLite (`backend/`)
- **Frontend**: Vue 3 + TypeScript + Tailwind CSS v4 (`vue/`) — 旧端,不再演进
- **Desktop (legacy)**: Electron wrapper (`electron/`) — 旧端,不再演进
- **Mac (main)**: Native SwiftUI app (`MyNote/`) — GRDB 直读共享 SQLite,**不依赖 backend 运行**
- **Android**: Native Kotlin/Compose app with Room DB + offline-first sync (`android/`, same git repo as backend/vue)
- **PWA**: Workbox service worker with offline caching (`vue/vite.config.ts`)
- **No auth** — designed for LAN use only

### Backend

Entry point: `backend/api.py` → runs uvicorn on port 8002. App initialized in `backend/app/__init__.py` with CORS (all origins), static mounts (`/uploads`, `/data`), rotating file logger, and router registration.

Key env vars:
- `DATA_ROOT` — data directory (required, no default), contains SQLite DB (`db.sqlite3`), uploads, thumbnails
- `FFMPEG_PATH` / `FFPROBE_PATH` — paths to ffmpeg binaries

**配置来源 / 切 instance**:`app/config.py` 在 import 时 `load_dotenv(backend/.env, override=False)`,优先级 高→低 = 真实环境变量 / `python api.py --data-root <path>` > `backend/.env`。因为 `app.models → app.config`,**所有**走 `from app.*` 的入口(api.py / alembic / `scripts/*` 如 import_bilibili)都自动跟随同一份 `.env`,无需各自配。一个 instance == 一个 `DATA_ROOT`(各自独立的 db/repositories.json/thumbs);日常切 instance 只改 `backend/.env` 里 `DATA_ROOT` 那行(注释切换)再重启。`backend/.env` 已 gitignored,模板见 `backend/.env.example`(复制即用)。`DB_NAME` 已废弃。

Routers (registered via `backend/app/routers/__init__.py:all_routers`): `actor`, `message`, `media`, `files`, `tags`, `sync`, `admin`, `dashboard`, `todos`.

Services:
- `media_service.py` — file hashing (Blake2b), deduplication, ffprobe info extraction, thumbnail generation. `process_file()` returns `{"media": Media, "is_new": bool}` — calls `db.flush()` (not commit) to get IDs; router commits. **Video cover sidecar 通用约定**:视频 `foo.mp4` 同目录如果有 `foo.cover.{jpg,jpeg,png,webp}`(case-insensitive),会被自动用作 thumb,优先于 ffmpeg 抽帧;失败时 fallback 抽帧。这是后端的通用接口 —— 任何批量导入(bilibili / youtube / 本地相册 / …)只要把 cover 放在视频旁边即可,无需写脚本覆盖缩略图。见 `_find_video_cover_sidecar`。
- `message_service.py` — `#hashtag` auto-extraction (regex `#[\w\u4e00-\u9fff]+`) from message text. Web/HTTP path uses full replacement (`merge=False`); sync-apply path from Android uses `merge=True` to preserve manually-added tags. Also handles media position reordering.
- `base.py` — static CRUD methods (`get_all`, `get_by_id`, `create`, `update`, `delete`) accepting SQLAlchemy model type.

DB session: `get_db()` generator in `models/__init__.py`, injected via `Depends(get_db)`. Configured with `autocommit=False`, `autoflush=False`.

Supported media types (in `config.py`): `.mp4` (video), `.jpg`/`.jpeg`/`.png`/`.gif` (image).

### Sync (Backend ↔ Android)

Single-user LAN-only model — no LWW conflict resolution, no SSE.

- **Pull**: `GET /sync/changes?since=<ISO>&since_id=<int>` — incremental from `SyncLog`. Composite cursor `(timestamp, id)` to avoid same-millisecond skips. Same-page dedup keeps DELETE over later UPSERT. Returns 410 if `since` exceeds `SYNC_LOG_RETENTION_DAYS=365`.
- **Push**: `POST /api/sync/apply` — Android Outbox batches mutations; backend applies all in a single transaction, rolls back on any failure. Upserts unconditionally overwrite (no `updated_at` comparison).
- **SyncLog tracking**: `services/sync_log_service.py` registers SQLAlchemy `after_flush` listener to record `Message`/`Actor`/`Media`/`Tag` mutations. `Message.tags` / `Media.tags` collection events bump host `updated_at` so tag-association changes show up in SyncLog.

### Pagination

Two cursor flavors:
1. **Simple ISO cursor** (Messages): cursor = `created_at.isoformat()`. Supports bidirectional: `direction=forward` with `prev_cursor`/`has_more_before` for calendar date jumps.
2. **Composite cursor** (Media page): format `"{created_at}|{position}"` — disambiguates multiple media sharing the same `created_at`. Both fields `DESC`.

All endpoints fetch `limit + 1` rows to detect `has_more`.

### Frontend

Vue 3.5 with `<script setup>` + TypeScript. No Pinia/Vuex — state via composables + localStorage.

Key composables:
- `useApi.ts` — typed fetch wrapper (`api.get/post/put/patch/del`), `useInfiniteScroll` with IntersectionObserver (200px rootMargin)
- `useToast.ts` — singleton reactive toast (success/error/info)
- `useTheme.ts` — dark/light mode toggle, persisted to localStorage, applies `.dark` class

API base URL hardcoded in `vue/src/utils/constants.ts` pointing to `http://127.0.0.1:8002`.

Routes: `/` (Message feed), `/media` (grid), `/actor` (list), `404` catch-all. All views use `<keep-alive>` caching.

UI: Tailwind v4 (Vite plugin), HeadlessUI, Vidstack (video player), v-calendar. Mobile-first responsive (sidebar hidden on mobile, bottom nav shown). Dark purple gradient background.

Media path/URL fields (filled by `MediaUrlMixin._fill_urls` in `app/schemas/base.py`):

| 字段              | 语义                                         | 谁消费              |
|-------------------|----------------------------------------------|---------------------|
| `repo_id`         | repository id                                 | 全员                |
| `file_path`       | 相对 repo 根的 forward-slash 路径(DB 权威)  | Mac 自己拼          |
| `local_file_path` | 绝对本地路径(`repo_root + file_path`)        | Vue / Electron      |
| `local_thumb_path`| 绝对本地路径 `{DATA_ROOT}/thumbs/{id}.webp` | Vue / Electron  |
| `file_url`        | 相对 URL `/{repo_id}/{file_path}`            | Android(拼 baseUrl) |
| `thumb_url`       | 相对 URL `/data/thumbs/{id}.webp`            | Android(拼 baseUrl) |

URL 都是**相对**的 —— 客户端用自己 sync 时配的 backend baseUrl 拼绝对 URL,这样换网段/host 不会有缓存污染。`/data` URL 前缀通过 StaticFiles 直接挂到 `DATA_ROOT` 根(所以 `/data/thumbs/x.webp` 物理对应 `DATA_ROOT/thumbs/x.webp`)。Actor 头像同步:`avatar_url` → `/data/actor_cover/{id}.webp`。

### Electron

Loads Vue dev server (`http://localhost:5173`) in dev, bundled dist in production. `webSecurity: false` to allow local file video playback. Preload script exposes `window.electronAPI.openFileDialog()` via IPC context bridge. Message.vue detects Electron via `navigator.userAgent`.

### Mac (MyNote/)

SwiftUI app with **direct read-only access** to the shared SQLite database via GRDB.swift — does NOT require backend to be running.

- Entry: `MyNote/MyNote/MyNoteApp.swift` — on launch, calls `LocalDatabase.shared.open(rootURL:)` with the user-chosen `DATA_ROOT`. First launch shows `OnboardingView` with `NSOpenPanel` to pick the directory; path persisted to `UserDefaults.dataRoot`.
- Data layer: `LocalDatabase` (singleton `DatabaseQueue`, `readonly = true`) → `MediaRepository` (composite cursor `(created_at, id)` paging, batch tag loading) → `MediaSource` protocol with `LocalMediaSource` (default) and `APIMediaSource` (HTTP fallback, kept for debugging).
- Models: `MediaRecord.swift` maps the `media` table 1:1 with backend SQLAlchemy schema (snake_case via `CodingKeys`). `Media` UI struct in `Models.swift` has `localThumbURL` / `localFileURL` computed props that resolve against `Settings.dataRoot`.
- UI: main window = `SidebarView` (left 200pt, fixed) + content area (right, fills). `SidebarView` is a `List(selection:)` with three `AppTab` entries (home / messages / media); default selection is `.media`. `AppTab` enum (title + SF Symbol) is the single source of truth. Content area renders `HomePlaceholderView` / `MessagesPlaceholderView` / `MediaLibraryView` based on selection. `MediaLibraryView` (4-col grid) is fully implemented; home / messages are blank placeholders to be filled by future changes. `FeedView` (message feed) is dropped from target.
- Thumbnails: `LocalImageLoader` (actor + `NSCache<NSNumber, NSImage>`) decodes webp off the main thread; replaces `AsyncImage` to avoid re-decoding on scroll. Requires macOS 14+ for native webp.
- Detail view: `NSImage` for images, `AVPlayer` for videos, both reading local file URLs.
- **Mac is read-only in first phase** — no starred toggle, no upload. Write operations still go through backend HTTP if/when re-enabled.
- See `MyNote/MAC_TODO.md` for Xcode-side setup (SPM add GRDB, deployment target, target membership).
- **Xcode project uses `PBXFileSystemSynchronizedRootGroup` (Xcode 16+)** — files added to `MyNote/MyNote/` are auto-included in the target. No `.pbxproj` editing needed for new Swift files.

### Database Models

`Message` → `MessageMedia` (junction with position) → `Media` (deduplicated by file_hash). `Tag` linked to Message via `message_tag`, to Media via `media_tag`. `Actor` linked to Message via FK. `starred` fields use Integer 0|1 (not boolean) for SQLite compatibility.

Video chapter/preview fields on `Media`: `video_media_id` (self-FK to parent video), `frame_ms`, `start_ms`, `end_ms` — child rows represent extracted frames or chapter clips of a parent video.

## Development Commands

### Backend
```bash
cd backend
pip install -e .          # or: uv pip install -e .
python api.py             # starts on 0.0.0.0:8002
```

### Frontend
```bash
cd vue
pnpm install
pnpm dev                  # dev server on 0.0.0.0:5173
pnpm build                # vue-tsc type-check + vite production build
pnpm preview              # preview production build
```

### Electron (start Vue dev server first)
```bash
cd electron
npm install
npm run dev               # loads http://localhost:5173
npm run build             # electron-builder, packages backend + vue dist
```

## 账单分类(Transactions)

**自动关键词分类已废弃** —— `txn_category_rule` 表 + `transaction_service.DEFAULT_RULES` 准确率太低。现在走**每月人工(LLM)打标**流程。

- 分类体系(14 类)+ 判断原则 + 月度运行步骤:见 [`docs/bills-categories.md`](docs/bills-categories.md)。改类目/改规则**先改这个文件**,代码层无配置。
- 真相之源:`backend/scratch/bills_by_month/*.json`(已标好的逐月账单,必须保留)。DB 只是它的物化产物。
- 月度脚本(`backend/scripts/`):
  - `bills_split_by_month.py` — 扫 `slip/` 下 CSV/xlsx,按 `txn_time` 切分到 `scratch/bills_by_month/YYYY-MM.json`。⚠️ 会**重新生成**已有月份,标过的需先备份;只想跑新月可改脚本只读新文件。
  - `bills_print_month.py YYYY-MM` — 紧凑打印一个月待标记录(给 Claude 读)。
  - `bills_apply_categories.py` — 接受 `{biz_no: category}` JSON,写回到对应月份文件。未命中的 biz_no 会报错。
  - `bills_inject_labeled.py [--apply]` — 清空 `transaction` + `txn_category_rule`,按所有月份 JSON 重新注入。**先 dry-run,再加 `--apply`,apply 前手动备份 `Data/db.sqlite3`。**
- 月度 mapping 文件(`backend/scratch/mappings/YYYY-MM.py`)是 Claude 的产出物,保留下来便于回溯/重跑。
- 老的 `import_bills.py` CLI 不要再用 —— 它会走废弃的自动分类。

## Key Patterns

- Cursor pagination everywhere (not offset-based). Response shape: `{ items, next_cursor, has_more }`
- Frontend types in `vue/src/types.ts` — `CursorResponse<T>` generic wraps all paginated responses
- Media files are deduplicated by Blake2b hash; files >100MB use file size as hash
- Thumbnails stored as WebP in `{DATA_ROOT}/thumbs/{media_id}.webp`
- Uploads auto-organized by date: `{DATA_ROOT}/uploads/YYYY/MM/DD/`
- `#hashtag` text in messages is auto-parsed into Tag records on create/update (full replacement, orphan tags not auto-deleted)
- Services call `db.flush()` for intermediate IDs; routers call `db.commit()` once at the end
- Backend query patterns avoid N+1: bulk media counts via grouped subquery, tag counts via `outerjoin` + `group_by`
- Electron detection in frontend: `navigator.userAgent.indexOf('Electron')`
