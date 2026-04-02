# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Build debug APK
./gradlew assembleDebug

# Build release APK (uses debug keystore currently)
./gradlew assembleRelease

# Run unit tests
./gradlew test

# Run a single unit test class
./gradlew testDebugUnitTest --tests "com.example.myapplication.ExampleUnitTest"

# Run instrumented tests (requires emulator/device)
./gradlew connectedAndroidTest

# Clean build
./gradlew clean

# Lint check
./gradlew lint
```

## Architecture

**MVVM + Repository pattern** with offline-first sync via an Outbox model.

### Layer Overview

- **UI Layer** (`ui/`): Jetpack Compose screens, viewmodels, theme, components
- **Data Layer** (`data/`): Room database, DAOs, entities, repositories, sync services
- **Navigation** (`navigation/`): Compose Navigation with typed routes defined in `Routes` object

### Data Flow

```
Compose Screen → ViewModel (StateFlow / PagingData) → Repository → DAO (Room) → SQLite
                                                         ↓
                                                 SyncOutboxRepository (queues mutations)
                                                         ↓
                                                 SyncPushService → POST /api/sync/apply
```

Repositories write data locally via DAOs **and** enqueue a `SyncOutboxItem` for each mutation. The push service batches pending outbox items and sends them to the backend.

### Message List (Telegram-style)

The message list (`MessageListScreen`) uses a **Telegram-style reverse-chronological chat layout**:
- **Paging3** for infinite scroll: `MessageDao.getMessagesPaged()` returns `PagingSource<Int, MessageWithDetails>`, consumed via `Pager` → `Flow<PagingData>` → `collectAsLazyPagingItems()`
- **`reverseLayout = true`** on `LazyColumn` — newest messages at the bottom, scroll up for history
- **`MessageWithDetails`** (Room `@Relation` entity from `Relations.kt`) carries `message`, `actor`, `mediaList`, `tagList` in a single query
- **`MessageCard`** renders a Telegram-style card: media thumbnail grid (1–4+ images with "+N" overlay, video play icons/duration) + text (3 lines max) + actor name · time · star
- **Date separators** inserted between messages on different days
- **`onMessageClick`** signature is `(Long) -> Unit` (passes messageId, not the entity)
- Sort/filter bottom sheet removed — messages are always ordered by `createdAt DESC`

### Key Entities & Relationships

8 Room entities with many-to-many relationships via junction tables:
- **Actor** → Message (one-to-many via foreignKey, `SET_NULL` on delete)
- **Message** ↔ Media (many-to-many via `MessageMedia`, composite PK)
- **Message** ↔ Tag (many-to-many via `MessageTag`, composite PK)
- **Media** ↔ Tag (many-to-many via `MediaTag`, composite PK)
- **SyncOutboxItem** — offline mutation queue (UPSERT/DELETE operations)

#### Entity Fields

**Actor**: `id`, `name`, `description?`, `avatarPath?`, `createdAt`, `updatedAt`

**Message**: `id`, `text?`, `actorId?` (FK→Actor), `starred` (Boolean), `source?`, `createdAt`, `updatedAt`

**Media**: `id`, `remoteMediaUrl?`, `remoteThumbnailUrl?`, `localMediaPath?`, `localThumbnailPath?`, `isDownloaded`, `downloadedAt?`, `fileHash` (unique, non-null), `fileSize?` (Long), `mimeType?`, `width?`, `height?`, `durationMs?` (Long, milliseconds), `rating` (Int 0-5), `starred` (Boolean), `viewCount`, `lastViewedAt?`, `createdAt`, `updatedAt`

**Tag**: `id`, `name` (unique), `category?`, `color?`, `createdAt`, `updatedAt`

**Junction tables**: `MessageMedia` (messageId+mediaId PK, position, createdAt), `MessageTag` (messageId+tagId PK), `MediaTag` (mediaId+tagId PK)

All junction table columns use **camelCase** naming (no `@ColumnInfo` overrides).

### Dependency Injection

Manual singleton pattern via `DatabaseManager` (not Hilt, despite Hilt being in the version catalog). `DatabaseManager` provides access to the database, all DAOs, and all repositories.

### Database

- Room database at **version 27** (`AppDatabase.kt`)
- Migration strategy: **fallback to destructive migration** (`DatabaseMigrations.kt`)
- KSP is used for Room annotation processing

## Tech Stack

- **Language**: Kotlin 2.0.21, JVM target 11
- **UI**: Jetpack Compose (BOM 2024.09.00) + Material3 with dynamic theming
- **Database**: Room 2.6.1 with KSP (includes `room-paging` for PagingSource support)
- **Pagination**: Paging3 3.3.6 (`paging-runtime` + `paging-compose`)
- **Navigation**: Compose Navigation 2.7.5
- **Networking**: Retrofit 2.9.0 + Gson
- **Image loading**: Coil 2.5.0
- **Video playback**: Media3 ExoPlayer 1.2.0
- **Build**: AGP 8.13.1, Gradle 8.13, version catalog (`gradle/libs.versions.toml`)

## Project Conventions

- Package: `com.example.myapplication`
- Debug builds use `.debug` applicationId suffix
- UI follows Instagram/Pinterest aesthetic — staggered grids, gradient colors, floating bottom nav
- Message list uses **Telegram-style** chat layout — reverse chronological, Paging3, bottom-anchored
- Bottom nav visibility controlled via `CompositionLocal` (`LocalBottomBarVisible`)
- Screen transitions use custom slide/fade animations (`NavigationAnimations.kt`)
- Sync entity types: `ACTOR`, `MEDIA`, `MESSAGE`, `TAG`; operations: `UPSERT`, `DELETE`
- Backend sync contract documented in `docs/sync-apply-prompt.md`
