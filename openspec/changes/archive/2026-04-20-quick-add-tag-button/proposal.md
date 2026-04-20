## Why

目前给 Message 添加 tag 必须通过键盘在 textarea 中手动输入 `#` 触发自动补全，操作步骤多、不直观。需要一个纯鼠标操作的快捷方式，让用户一键从已有 tag 列表中选择并自动插入到 message text 开头。

## What Changes

- 在 MessageCard 的操作按钮区域（详情/编辑按钮上方）新增一个「添加 Tag」按钮
- 点击按钮弹出 tag 选择弹窗（显示已有 tag 列表，支持搜索过滤）
- 选择 tag 后自动将 `#tagname` 插入到 message text 的开头，并调用 API 更新
- 全程只需鼠标操作，无需键盘输入

## Capabilities

### New Capabilities
- `quick-add-tag`: MessageCard 上的快捷 tag 添加按钮及弹窗选择交互

### Modified Capabilities

## Impact

- 前端：MessageCard.vue 新增按钮和弹窗组件
- 前端：需要获取全局 tag 列表（复用已有 `/tags` API）
- 后端：无变更，复用现有 PATCH `/messages/{id}` 接口（更新 text 后自动同步 tags）
