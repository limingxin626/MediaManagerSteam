## 1. Tag 选择弹窗组件

- [x] 1.1 创建 TagPickerPopover.vue 组件：Popover 容器 + 搜索输入框 + tag 列表（按 message_count 降序），已关联 tag 视觉标记，点击触发 emit
- [x] 1.2 实现搜索过滤逻辑：输入文字实时过滤 tag 列表

## 2. MessageCard 集成

- [x] 2.1 在 MessageCard hover 操作栏添加「添加 Tag」图标按钮，点击打开 TagPickerPopover
- [x] 2.2 实现 tag 插入逻辑：将 `#tagname ` 插入到 text 开头（智能检测已有 hashtag 序列位置），重复 tag 跳过并 toast 提示
- [x] 2.3 调用 PATCH `/messages/{id}` 更新 text，成功后刷新本地 message 数据
