## Context

消息详情面板是 Message.vue 中右侧 50% 宽度的区域，点击 MessageCard 后展开。当前仅有：文本（markdown）、标签芯片、3列媒体网格、拆分功能、底部日期。缺少编辑/删除/收藏等操作，与 MessageCard 的功能不对齐。

## Goals / Non-Goals

**Goals:**
- 详情面板拥有与 MessageCard 对等的操作能力（编辑、删除、收藏）
- 媒体网格根据数量自适应列数
- 清晰的信息层级和视觉分隔
- 演员信息展示

**Non-Goals:**
- 不改动后端 API
- 不重构为独立组件（保持在 Message.vue 内）
- 不改动 MessageCard 本身

## Decisions

1. **操作栏放在 header 区域** — 编辑/删除/收藏按钮放在详情面板 header 右侧，与关闭按钮一行。拆分按钮保留原位。这样操作始终可见，不需滚动。

2. **媒体网格自适应** — 1张：单张大图；2张：2列；3+张：3列。使用动态 grid-cols class 切换。

3. **日期移入 header** — 日期从底部移到标题旁边，显示为副标题样式，header 改为两行布局（标题+日期 / 操作按钮）。

4. **演员展示** — 如果消息有关联演员，在文本下方显示演员头像+名称，可点击跳转。

## Risks / Trade-offs

- header 按钮较多时可能拥挤 → 使用图标按钮，无文字标签
- 详情面板内删除消息后需要同步更新列表状态 → 复用已有的 handleDeleteMessage 逻辑
