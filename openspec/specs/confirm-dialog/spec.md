## ADDED Requirements

### Requirement: 统一确认弹窗组件
系统 SHALL 提供 `ConfirmDialog.vue` 组件和 `useConfirm()` composable，替换所有 `window.confirm()` 调用。

composable API：
```typescript
const { confirm } = useConfirm()
const ok = await confirm({
  title: string,
  message: string,
  confirmText?: string,    // 默认 "确认"
  cancelText?: string,     // 默认 "取消"
  danger?: boolean         // true 时确认按钮为红色
})
```

弹窗 SHALL 基于 HeadlessUI Dialog，支持 Escape 关闭、点击遮罩关闭、焦点锁定。

#### Scenario: 删除消息确认
- **WHEN** 用户点击删除按钮
- **THEN** 弹出确认弹窗，标题 "确认删除"，确认按钮为红色 danger 风格
- **WHEN** 用户点击 "确认"
- **THEN** `confirm()` 返回 `true`，执行删除操作

#### Scenario: 用户取消操作
- **WHEN** 用户在确认弹窗中点击 "取消" 或按 Escape
- **THEN** `confirm()` 返回 `false`，不执行操作

#### Scenario: 点击遮罩关闭
- **WHEN** 用户点击弹窗外部遮罩区域
- **THEN** 弹窗关闭，`confirm()` 返回 `false`
