## Context

当前 Message 的 tag 管理依赖 MessageComposeDialog 中的 textarea + `#` 键触发自动补全。这要求用户打开编辑弹窗→定位光标→键盘输入 `#`→选择 tag→保存，步骤繁琐。

MessageCard 已有操作按钮（编辑、详情等），可以在同一区域添加快捷入口。后端 PATCH `/messages/{id}` 已支持通过更新 text 自动同步 tags，无需后端改动。

## Goals / Non-Goals

**Goals:**
- 提供纯鼠标操作的 tag 添加方式
- 从已有 tag 列表中选择，避免手动输入和拼写错误
- 选中后自动在 message text 开头插入 `#tagname `，调用 API 更新

**Non-Goals:**
- 不做 tag 删除/管理功能
- 不改变现有键盘输入 `#` 自动补全流程
- 不修改后端 API

## Decisions

**1. 交互方式：Popover 弹窗而非 Modal**
- Popover 轻量、就地显示，适合快速操作
- 复用 HeadlessUI 的 Popover 组件，与项目现有 UI 一致
- 替代方案：Modal 弹窗太重，下拉菜单不方便搜索

**2. Tag 列表来源：复用 `/tags` API**
- 已有 `GET /tags` 返回所有 tag（含 message_count），直接复用
- 按使用频率排序，最常用的排在前面
- 已关联的 tag 标记为已添加状态，防止重复

**3. 插入位置：text 开头**
- 用户明确要求插入到 text 开头
- 格式：`#tagname \n` + 原有 text（如果开头已有 tag 则直接prepend到开头加空格，否则在开头新建一行）

**4. 按钮位置：MessageCard hover 操作栏**
- 与现有编辑/详情按钮同级，保持 UI 一致性

## Risks / Trade-offs

- [重复 tag] → 插入前检查 text 中是否已包含该 `#tagname`，已有则跳过并 toast 提示
- [text 格式干扰] → 始终插入在最开头并加空格分隔，不会破坏原有内容
