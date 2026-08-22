## Context

SystemMedia 以 `image:<id>` / `video:<id>` 作为当前设备内稳定身份。现有 `Tag` 表可复用，但 `media_tag` 外键绑定 Room `Media.id`，不能用于 MediaStore 项目。项目 DB 使用 destructive fallback，因此增加实体时提升版本即可。

## Goals / Non-Goals

**Goals:**
- 本机收藏与标签持久化。
- 列表和预览状态即时一致。
- 支持收藏与标签筛选。
- 不影响现有 Room Media 标签关系。

**Non-Goals:**
- 跨设备同步或上传。
- 写入 MediaStore 的系统收藏。
- 基于 hash 的跨设备身份匹配。
- 删除系统文件或清理孤立元数据。

## Decisions

### 1. 两张本机表

`system_media_metadata(stableKey PK, contentUri, starred, updatedAt)`；`system_media_tag(systemMediaKey, tagId)` 使用复合主键，并对 metadata、tag 设置级联外键。

### 2. 本机 repository 原子更新

收藏时 upsert metadata；设置标签时先确保 metadata 存在，再在 transaction 中替换 tag link。repository 不依赖 Outbox。

### 3. UI 合并模型

新增 `SystemMediaWithMetadata(media, starred, tags)`。ViewModel combine MediaStore 列表、metadata flow、tag-link flow 和筛选状态，产生可显示列表；保留原始完整列表用于预览分页。

### 4. 复用 TagSelectorDialog

列表或预览通过现有多选对话框编辑当前系统媒体标签。筛选使用单选标签菜单与收藏开关，避免引入新页面。

### 5. 共享 viewer 可选系统操作

中立 viewer item 携带 nullable starred；共享 viewer 已通过 nullable callback 控制收藏按钮。系统 adapter 提供本机收藏回调，不提供上传、删除或编辑文件操作。标签按钮放在系统 detail adapter 的覆盖层或共享 viewer 可选 action 中。

## Risks / Trade-offs

- MediaStore ID 在文件删除重建后可能变化，本阶段接受本机身份限制。
- destructive migration 会清空现有 Room 数据，符合项目当前升级策略。
- 大量 tag-link 合并应批量读取，禁止逐媒体 DAO 查询。

## Migration Plan

1. 注册实体/DAO并将 DB 32 升至 33。
2. 添加 repository 与 DatabaseManager wiring。
3. 合并 ViewModel 状态和 mutation。
4. 接入列表、预览及筛选 UI。
5. 测试并构建。
