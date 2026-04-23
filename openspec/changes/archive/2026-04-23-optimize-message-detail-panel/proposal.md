## Why

消息详情面板（Message.vue 右侧）当前只是简单堆叠文本、标签和媒体网格，缺少操作按钮（编辑、删除、收藏）、信息层级不清晰、排版拥挤。MessageCard 已经打磨到位，但点开详情后体验明显下降，需要对齐卡片的交互质量。

## What Changes

- 重新设计详情面板布局：增加信息层级，改善间距和视觉分隔
- 添加操作按钮栏：编辑、删除、收藏消息（与 MessageCard 功能对齐）
- 改善媒体网格显示：自适应列数（1张大图/2张两列/3+三列），更好的间距
- 添加演员信息展示（如有关联）
- 优化文本排版：更好的 markdown 渲染样式
- 日期显示移到顶部 header 区域，释放底部空间

## Capabilities

### New Capabilities
- `message-detail-panel`: 消息详情面板的完整布局、操作栏、媒体网格自适应、演员展示

### Modified Capabilities

## Impact

- `vue/src/views/Message.vue` — 详情面板模板和相关方法
- 无后端改动，无 API 改动
- 无破坏性变更
