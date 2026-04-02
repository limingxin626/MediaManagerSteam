# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal media management app with an Instagram-like feed architecture. Self-hosted on LAN. The project is in Chinese (comments, docs, UI strings).

## Architecture

- **Backend**: FastAPI + SQLAlchemy + SQLite (`backend/`)
- **Frontend**: Vue 3 + TypeScript + Tailwind CSS v4 (`vue/`)
- **Desktop**: Electron wrapper (`electron/`)
- **Android**: Native Kotlin/Compose app with Room DB + offline-first sync (`android/`, separate git repo)
- **PWA**: Workbox service worker with offline caching (`vue/vite.config.ts`)
- **No auth** — designed for LAN use only

### Backend

Entry point: `backend/api.py` → runs uvicorn on port 8002. App initialized in `backend/app/__init__.py` with CORS (all origins), static mounts (`/uploads`, `/data`), rotating file logger, and router registration.

Key env vars:
- `ASKTAO_DATA_ROOT` — data directory (default `E:/AskTao`), contains SQLite DB (`db_new.sqlite3`), uploads, thumbnails
- `FFMPEG_PATH` / `FFPROBE_PATH` — paths to ffmpeg binaries

Routers: `/messages`, `/media`, `/actors`, `/tags`, `/files`

Services:
- `media_service.py` — file hashing (Blake2b), deduplication, ffprobe info extraction, thumbnail generation. `process_file()` returns `{"media": Media, "is_new": bool}` — calls `db.flush()` (not commit) to get IDs; router commits.
- `message_service.py` — `#hashtag` auto-extraction (regex `#[\w\u4e00-\u9fff]+`) from message text doing full tag replacement (not additive), media position reordering.
- `base.py` — static CRUD methods (`get_all`, `get_by_id`, `create`, `update`, `delete`) accepting SQLAlchemy model type.

DB session: `get_db()` generator in `models/__init__.py`, injected via `Depends(get_db)`. Configured with `autocommit=False`, `autoflush=False`.

Supported media types (in `config.py`): `.mp4` (video), `.jpg`/`.jpeg`/`.png`/`.gif` (image).

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

API base URL hardcoded in `vue/src/utils/constants.ts` pointing to `http://192.168.31.146:8002`.

Routes: `/` (Message feed), `/media` (grid), `/actor` (list), `404` catch-all. All views use `<keep-alive>` caching.

UI: Tailwind v4 (Vite plugin), HeadlessUI, Vidstack (video player), v-calendar. Mobile-first responsive (sidebar hidden on mobile, bottom nav shown). Dark purple gradient background.

Pydantic schema validators auto-fill URL fields: `thumb_url` → `/data/thumbs/{id}.webp`, `avatar_url` → `/data/actor_cover/{id}.webp`.

### Electron

Loads Vue dev server (`http://localhost:5173`) in dev, bundled dist in production. `webSecurity: false` to allow local file video playback. Preload script exposes `window.electronAPI.openFileDialog()` via IPC context bridge. Message.vue detects Electron via `navigator.userAgent`.

### Database Models

`Message` → `MessageMedia` (junction with position) → `Media` (deduplicated by file_hash). `Tag` linked to Message via `message_tag`. `Actor` linked to Message via FK. `starred` fields use Integer 0|1 (not boolean) for SQLite compatibility.

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

## Key Patterns

- Cursor pagination everywhere (not offset-based). Response shape: `{ items, next_cursor, has_more }`
- Frontend types in `vue/src/types.ts` — `CursorResponse<T>` generic wraps all paginated responses
- Media files are deduplicated by Blake2b hash; files >100MB use file size as hash
- Thumbnails stored as WebP in `{DATA_ROOT}/data/thumbs/{media_id}.webp`
- Uploads auto-organized by date: `{DATA_ROOT}/uploads/YYYY/MM/DD/`
- `#hashtag` text in messages is auto-parsed into Tag records on create/update (full replacement, orphan tags not auto-deleted)
- Services call `db.flush()` for intermediate IDs; routers call `db.commit()` once at the end
- Backend query patterns avoid N+1: bulk media counts via grouped subquery, tag counts via `outerjoin` + `group_by`
- Electron detection in frontend: `navigator.userAgent.indexOf('Electron')`
