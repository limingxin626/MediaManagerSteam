## Context

Message.vue 当前使用右下角 FAB 按钮触发 `MessageComposeDialog`。用户希望改为底部居中的输入框样式入口，点击后弹出同样的对话框。

## Goals / Non-Goals

**Goals:**
- 用底部居中的假输入框替代 FAB，作为创建消息的唯一入口
- 点击输入框弹出现有的 `MessageComposeDialog`
- 桌面端和移动端都正常显示，不与底部导航栏重叠

**Non-Goals:**
- 不在输入栏内实现实际输入功能
- 不修改 `MessageComposeDialog` 本身的逻辑

## Decisions

1. **输入栏位置**：固定在消息流底部（`sticky bottom-0` 或 feed 区域内底部），居中显示。桌面端在 feed 列底部；移动端在底部导航栏上方。
2. **实现方式**：直接在 Message.vue 内添加一个 div 模拟输入框样式，绑定 `@click="openCreateDialog"`，无需新组件。
3. **样式**：圆角输入框外观，带 placeholder 文字如"写点什么..."，右侧可选附加图标（如"+"）。背景使用 `bg-[var(--bg-card)]` 配合边框。
4. **移动端适配**：输入栏在移动端需要给 BottomNavBar 留出空间（通过 `mb-20 md:mb-0` 或类似方式）。

## Risks / Trade-offs

- 输入栏占据底部固定空间，消息流可视区域略微减小，但交互便利性提升值得。
