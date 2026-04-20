## 1. 后端API

- [x] 1.1 新增 `POST /messages/{id}/media` 端点：接收文件上传，调用process_file处理，创建MessageMedia关联，position为当前最大值+1
- [x] 1.2 新增 `DELETE /messages/{id}/media/{media_id}` 端点：删除MessageMedia关联记录，重排剩余媒体position
- [x] 1.3 验证PATCH端点已有的media_order功能可正常工作

## 2. 前端编辑对话框改造

- [x] 2.1 MessageComposeDialog编辑模式接收并展示已有媒体缩略图网格
- [x] 2.2 编辑模式增加文件选择按钮，选择后显示本地预览缩略图
- [x] 2.3 已有媒体缩略图增加删除按钮，点击调用DELETE接口
- [x] 2.4 实现拖拽排序功能，拖拽结束后调用PATCH media_order更新顺序
- [x] 2.5 提交编辑时，逐个上传新文件到POST端点

## 3. 数据流对接

- [x] 3.1 Message.vue的openEditDialog传递message的media_items到对话框
- [x] 3.2 编辑完成后刷新消息数据以反映媒体变更
