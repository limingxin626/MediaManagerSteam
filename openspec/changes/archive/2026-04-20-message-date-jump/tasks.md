## 1. 依赖与准备

- [x] 1.1 确认 v-calendar 已安装，若未安装则 `pnpm add v-calendar@next`
- [x] 1.2 在 Vue 项目中注册 v-calendar 组件和样式

## 2. 日历弹窗 UI

- [x] 2.1 将 Message.vue 顶部浮动日期徽章改为可点击按钮
- [x] 2.2 添加 Popover 弹窗包裹 v-calendar 日历组件
- [x] 2.3 实现日历深色模式适配样式

## 3. 日历数据加载

- [x] 3.1 日历打开时调用 `/messages/dates` 加载当前月份消息分布
- [x] 3.2 用 v-calendar attributes 标记有消息的日期（圆点）
- [x] 3.3 切换月份时按需加载并缓存月份数据
- [x] 3.4 无消息日期设为禁用不可选

## 4. 日期跳转逻辑

- [x] 4.1 选择日期后以该日期 ISO 字符串作为 cursor 调用 `/messages/with-detail`
- [x] 4.2 清空当前消息列表，加载目标日期消息并显示
- [x] 4.3 设置 `isViewingHistory` 状态和 `forwardCursor`，启用双向滚动
- [x] 4.4 关闭日历弹窗，滚动到加载的消息顶部
