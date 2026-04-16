## 1. 替换 FAB 为底部输入栏

- [x] 1.1 在 Message.vue 中移除 FAB 按钮（`<!-- FAB: New Message -->` 部分）
- [x] 1.2 在消息流区域底部（scrollable content 之后、MessageComposeDialog 之前）添加底部输入栏：固定在 feed 列底部，居中显示，圆角输入框样式，placeholder "写点什么..."，点击调用 `openCreateDialog()`
- [x] 1.3 输入栏样式：`bg-[var(--bg-card)]` 背景、边框、圆角、右侧 "+" 图标，与整体暗色主题一致

## 2. 移动端适配

- [x] 2.1 确保输入栏在移动端不与 BottomNavBar 重叠（添加底部间距 `mb-20 md:mb-0` 或类似处理）
- [x] 2.2 验证桌面端和移动端布局正确显示
