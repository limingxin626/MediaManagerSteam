## Why

Message编辑目前只支持修改文本和日期，无法添加新媒体文件。用户需要为已有消息补充图片/视频时，只能通过拆分合并等间接方式操作，体验不佳。

## What Changes

- 编辑对话框（MessageComposeDialog）增加文件选择区域，支持在编辑模式下添加新媒体
- 后端 PATCH `/messages/{id}` 端点扩展，支持接收新文件并处理为媒体记录
- 新增媒体自动追加到消息已有媒体列表末尾（position递增）
- 编辑对话框中展示已有媒体缩略图，支持删除已有媒体
- 支持拖拽排序调整媒体顺序

## Capabilities

### New Capabilities
- `message-edit-media`: 消息编辑时添加、删除、排序媒体文件的完整功能

### Modified Capabilities

## Impact

- **后端**: `message.py` router 的 PATCH 端点需要改为接收 multipart/form-data 或分步调用
- **前端**: `MessageComposeDialog.vue` 需要扩展编辑模式UI；`Message.vue` 需要传递已有媒体数据到对话框
- **API契约**: PATCH `/messages/{id}` 的请求格式变更
