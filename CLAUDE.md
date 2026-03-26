# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal media management app with an Instagram-like feed architecture. Self-hosted on LAN. The project is in Chinese (comments, docs, project status).

## Architecture

- **Backend**: FastAPI + SQLAlchemy + SQLite (`backend/`)
- **Frontend**: Vue 3 + TypeScript + Tailwind CSS v4 (`vue/`)
- **Desktop**: Electron wrapper (`electron/`)
- **No auth** — designed for LAN use only

### Backend

Entry point: `backend/api.py` → runs uvicorn on port 8002. App initialized in `backend/app/__init__.py` with CORS (all origins), static mounts, and router registration.

Key env vars:
- `ASKTAO_DATA_ROOT` — data directory (default `E:/AskTao`), contains SQLite DB (`db_new.sqlite3`), uploads, thumbnails
- `FFMPEG_PATH` / `FFPROBE_PATH` — paths to ffmpeg binaries

Routers: `/messages`, `/media`, `/actors`, `/tags`, `/files`

Services:
- `media_service.py` — file hashing (Blake2b), deduplication, ffprobe info extraction, thumbnail generation
- `message_service.py` — `#hashtag` auto-extraction from message text, media reordering

Pagination is cursor-based using ISO datetime strings. Media uses composite cursor (`created_at|position`).

### Frontend

Vue 3.5 with `<script setup>` + TypeScript. No Pinia/Vuex — state via composables + localStorage.

Key composables:
- `useApi.ts` — fetch wrapper (`api.get/post/put/patch/del`), `useInfiniteScroll` with IntersectionObserver
- `useToast.ts` — singleton reactive toast (success/error/info)

API base URL hardcoded in `vue/src/composables/constants.ts` pointing to `192.168.31.146:8002`.

Routes: `/` (Message feed), `/media` (grid), `/actor` (list), `404` catch-all. All views use keep-alive caching.

UI: Tailwind v4 (Vite plugin), HeadlessUI, Vidstack (video player), v-calendar. Mobile-first responsive (sidebar hidden on mobile, bottom nav shown).

### Database Models

`Message` → `MessageMedia` (junction with position) → `Media` (deduplicated by file_hash). `Tag` linked to Message via `message_tag`. `Actor` linked to Message via FK.

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
pnpm build                # type-check + production build
pnpm preview              # preview production build
```

### Electron
```bash
cd electron
npm install
npm run dev               # dev with live reload
npm run build             # package for distribution
```

## Key Patterns

- Cursor pagination everywhere (not offset-based). Response shape: `{ items, next_cursor, has_more }`
- Frontend types in `vue/src/types.ts` — `CursorResponse<T>` generic wraps all paginated responses
- Media files are deduplicated by Blake2b hash; files >100MB use file size as hash
- Thumbnails stored as WebP in `{DATA_ROOT}/data/thumbs/{media_id}.webp`
- Uploads auto-organized by date: `{DATA_ROOT}/uploads/YYYY/MM/DD/`
- `#hashtag` text in messages is auto-parsed into Tag records on create/update
