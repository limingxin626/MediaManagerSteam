# Android 与 Backend 全局 Media 同步计划

## 目标

`Media` 是跨端共享的全局逻辑实体。Backend 的 `RepositoryFile` 和 Android
的 MediaStore 项只是各端可访问的物理文件地址。

```text
                        Media
                   全局逻辑媒体
                     /       \
                    /         \
       RepositoryFile       Android MediaStore
       Backend 物理文件      Android 本地物理文件
```

Backend 不需要保存 Android 的 `content://` 地址，也不需要在
`repositories.json` 中配置 Android Repository。Android 在本地维护
MediaStore 项与全局 `Media.id` 的映射。

## 核心约束

1. Backend 分配并维护全局 `Media.id`。
2. 跨端内容去重使用 `file_hash`，不使用 Android 本地自增 ID。
3. Android Room 本地主键与 Backend 全局 ID 分离，本地主键创建后不修改。
4. `RepositoryFile` 继续表示 Backend 可直接访问的物理文件。
5. Android 的 `contentUri`、本地原图路径和本地缩略图路径只保存在 Android。
6. Android 上传原文件后，为已有 Media 创建或匹配 `RepositoryFile`，不创建第二个
   Media。
7. Backend 保存 canonical thumbnail，Android 可保留它的本地离线副本。

## Backend 修改

### 1. 允许 Media 暂时没有 Backend 文件

将 `Media.repo_id` 和 `Media.file_path` 改为 nullable。

- 存在可用 `RepositoryFile` 时，这两个字段继续作为兼容用 canonical path。
- 只有 Android 本地文件时，两字段为空，`file_url` 为空。
- Android 后续上传原文件并创建 `RepositoryFile` 后，再设置 canonical path。

在 Mac、Vue 和现有 Backend 查询全部迁移到 RepositoryFile 之前，不删除这两个兼容
字段。

### 2. 增加批量 Media 注册接口

增加：

```http
POST /media/register
```

Android 分批提交 MediaStore 中媒体的逻辑元数据：

```json
{
  "items": [
    {
      "client_id": "android-generated-uuid",
      "client_key": "image:123",
      "file_hash": "abc123",
      "file_size": 456789,
      "mime_type": "image/jpeg",
      "width": 4000,
      "height": 3000,
      "duration_ms": null,
      "taken_at": "2026-09-01T10:20:30"
    }
  ]
}
```

Backend 按 `file_hash` 查找 Media：

- 命中时返回已有全局 ID。
- 未命中时创建没有 RepositoryFile 的 Media。
- 同一批请求或网络重试必须幂等。

响应返回本地标识到全局 ID 的映射：

```json
{
  "items": [
    {
      "client_id": "android-generated-uuid",
      "client_key": "image:123",
      "media_id": 817,
      "created": true
    }
  ]
}
```

### 3. 增加原文件和缩略图上传接口

增加原子 multipart 接口：

```http
POST /media/register-upload
```

请求包含：

- `client_id`
- `file_hash`
- 媒体元数据
- `original_file`
- `thumbnail_file`

Backend 在一个完整用例中：

1. 按 hash 创建或复用 Media。
2. 校验上传文件的实际 hash。
3. 保存或匹配 RepositoryFile。
4. 将缩略图保存为 `{DATA_ROOT}/thumbs/{media_id}.webp`。
5. 返回 `media_id`、`file_url`、`thumb_url` 和完整 Media 快照。

如果 Media 已经具有可用 RepositoryFile，不重复保存原文件；如果已有 canonical
thumbnail，则以 Backend 版本为准。

### 4. 调整同步快照

无 Backend 文件的 Media 仍进入 `/sync/changes`，但：

```json
{
  "id": 817,
  "file_url": null,
  "thumb_url": "/data/thumbs/817.webp"
}
```

所有 URL 构造逻辑必须处理 nullable canonical path，不能再无条件调用
`config.url_for(media.repo_id, media.file_path)`。

## Android 修改

### 1. 分离本地 ID 与全局 ID

Android `Media` 使用：

```kotlin
data class Media(
    val id: Long,
    val clientId: String,
    val globalId: Long?,
    // logical metadata...
)
```

- `id`：Room 本地主键，永不修改。
- `clientId`：Android 创建的 UUID，用于离线创建和幂等重试。
- `globalId`：Backend 返回的全局 `Media.id`。

为 `clientId`、非空 `globalId` 建立唯一索引。`MessageMedia`、`MediaTag`、
`MediaPerson` 等 Room 外键继续引用本地 `id`；同步 payload 使用 `globalId`。

需要编写正式 Room migration，不能依赖 destructive migration 清空已有映射和
Outbox。

### 2. 保存 MediaStore 映射

扩展 `SystemMediaMetadata` 或增加独立映射表：

```text
system_media_mapping
- stableKey
- contentUri
- localMediaId
- fileHash
- fileSize
- modifiedAt
- syncStatus
```

其中 `contentUri` 只在 Android 本地使用，不发送给 Backend。

### 3. 全量扫描与增量注册

使用 WorkManager：

```text
扫描 MediaStore
→ 与本地 mapping 比较
→ 为新增或变化文件计算 hash
→ 分批调用 /media/register
→ 保存返回的 globalId
→ 通过现有同步协议拉取逻辑元数据
```

首次全量扫描必须可暂停、重试和断点续传。只有文件大小或修改时间变化时才重新计算
hash。

### 4. 上传状态机

```text
LOCAL_ONLY
→ HASHING
→ PENDING_UPLOAD
→ UPLOADING
→ SYNCED
```

上传失败回到 `PENDING_UPLOAD`，重试时保持相同 `clientId`。上传成功后只更新
`globalId`、远程 URL 和状态，不修改 Room 主键。

## Thumbnail 规则

Backend thumbnail 是全局权威版本：

- 格式统一为 WebP。
- 固定最大尺寸和裁剪策略。
- 统一处理 EXIF orientation。
- 视频统一抽取时间点。
- 可增加 `thumbnail_hash` 或 `thumbnail_version` 判断 Android 本地副本是否过期。

Android 可以先生成 thumbnail 用于立即显示，并在上传原文件时一起提交。上传完成后
Android 使用 Backend 返回的 `thumb_url` 作为远程来源，本地文件作为离线副本。

## 删除语义

- Android 删除 MediaStore 文件：删除本地 mapping，不自动删除全局 Media。
- Backend 删除 RepositoryFile：只删除物理文件事实；Media 可继续保留。
- 用户明确执行全局删除：删除 Media，并通过 SyncLog 向各端发送 tombstone。
- 暂不追踪某个 Media 是否仍位于特定 Android 设备；如未来需要设备在线取文件或
  自动清理无副本 Media，再引入设备文件清单。

## 实施顺序

1. Backend 将 `Media.repo_id/file_path` 改为 nullable，并补齐无文件 Media 的 schema
   和 URL 行为。
2. 实现 `/media/register` 批量逻辑注册及幂等测试。
3. Android 增加 `clientId/globalId` 和 MediaStore mapping 的正式 Room migration。
4. 实现 WorkManager 全量扫描、hash 和分批注册。
5. 调整 Android Outbox，使同步使用 `globalId`。
6. 实现 `/media/register-upload`，原子保存原文件、RepositoryFile 和 thumbnail。
7. Android 接入上传状态机和 canonical thumbnail。
8. 最后逐步让 Vue、Mac 和 Backend 查询直接从 RepositoryFile 解析物理路径，减少对
   `Media.repo_id/file_path` 兼容字段的依赖。

## 验证范围

- 同一 hash 的 Android 和 Backend 文件映射到同一个 Media。
- 注册请求重试不会创建重复 Media。
- 无 RepositoryFile 的 Media 可以正常同步和展示逻辑元数据。
- 上传后为原 Media 创建 RepositoryFile，不产生第二个 Media。
- 上传 hash 不一致时拒绝绑定。
- thumbnail 上传失败不会留下成功状态或半完成记录。
- Android 上传成功后不修改 Room 主键，现有关联保持有效。
- Android 离线创建、进程重启和网络重试后仍使用相同 clientId。
- Android 删除本地系统文件不会误删全局 Media。
