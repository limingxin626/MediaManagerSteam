## 1. Room 存储

- [x] 1.1 新增 system media metadata 与 tag junction entities
- [x] 1.2 新增批量观察、收藏 upsert、标签替换 DAO
- [x] 1.3 注册 AppDatabase entities/DAO 并将版本提升至 33
- [x] 1.4 新增 local-only repository 并接入 DatabaseManager

## 2. 状态合并

- [x] 2.1 新增 SystemMediaWithMetadata UI 模型
- [x] 2.2 MediaViewModel 合并 MediaStore、metadata、tag links 与 Tag 列表
- [x] 2.3 实现收藏、设置标签、收藏筛选和标签筛选操作

## 3. UI

- [x] 3.1 Media 网格显示收藏状态并支持收藏切换
- [x] 3.2 Media 页增加收藏与 Tag 筛选
- [x] 3.3 系统预览接入本机收藏按钮
- [x] 3.4 系统媒体通过 TagSelectorDialog 查看和编辑标签

## 4. 验证

- [x] 4.1 添加 DAO/repository/view-model 纯逻辑测试
- [x] 4.2 运行 testDebugUnitTest 与 assembleDebug
- [x] 4.3 验证无 Outbox、上传或 MediaStore 写操作
- [ ] 4.4 真机验证列表/预览收藏一致和 Tag 组合筛选
