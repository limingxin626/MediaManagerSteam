## Context

当前MessageComposeDialog在编辑模式下只能修改text和created_at。媒体操作（添加/删除/排序）需要通过拆分合并等间接操作完成。后端PATCH端点仅接受JSON字段更新，不处理文件上传。

## Goals / Non-Goals

**Goals:**
- 编辑消息时可以添加新媒体文件（图片/视频）
- 编辑时可以删除已有媒体
- 编辑时可以拖拽调整媒体顺序
- 复用现有的media_service.process_file流程

**Non-Goals:**
- 不修改媒体文件本身（裁剪、滤镜等）
- 不改变创建消息的流程
- 不支持跨消息移动媒体（已有split功能覆盖）

## Decisions

### 1. 新增媒体使用独立POST端点，而非改造PATCH

**决定**: 新增 `POST /messages/{id}/media` 端点用于上传文件，PATCH端点不变。

**理由**: PATCH目前接受JSON，改为multipart/form-data会破坏现有调用方。独立端点职责清晰，前端可以逐个上传文件并展示进度。

**替代方案**: 改PATCH为multipart — 破坏性变更，且混合文本字段和文件上传增加复杂度。

### 2. 删除媒体使用 DELETE /messages/{id}/media/{media_id}

**决定**: 新增端点删除MessageMedia关联记录。仅解除关联，不删除Media文件本身（可能被其他消息引用）。

**理由**: 与现有RESTful风格一致。Media本体的清理由现有的orphan清理逻辑处理。

### 3. 排序复用现有media_order参数

**决定**: 复用PATCH端点已有的`media_order`字段来调整排序。

**理由**: 该功能已存在于后端，只需前端对接。

### 4. 前端编辑对话框内展示已有媒体

**决定**: 编辑模式打开时，传入message的media_items数据，在对话框中以缩略图网格展示，支持删除按钮和拖拽排序。新选择的文件追加在末尾。

**理由**: 用户需要看到完整媒体列表才能做出编辑决策。

## Risks / Trade-offs

- **[并发编辑]** 多客户端同时编辑同一消息可能冲突 → 可接受，单用户LAN场景
- **[文件上传失败]** 部分文件上传成功部分失败 → 逐个上传，失败时toast提示，已上传的保留
- **[大文件]** 大视频上传可能超时 → 复用现有上传机制，暂不特殊处理
