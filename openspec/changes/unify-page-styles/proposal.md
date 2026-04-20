## Why

三个主页面（Message、Media、Actor）在独立开发过程中积累了视觉风格不一致的问题：标题字号不统一（text-base / text-xl / text-2xl）、header 间距各异（py-2 / py-3 / py-4）、筛选按钮颜色混用（CSS 变量 vs 硬编码 pink-600）、内容区最大宽度不一致。这些差异让用户在页面间切换时感到割裂。

## What Changes

- 统一三个页面的 header 区域：一致的标题字号、间距、边框样式
- 统一筛选/过滤按钮的颜色方案，全部使用 CSS 变量 `--color-primary-*`，移除硬编码的 `pink-600`
- 统一内容区的 max-width 和 padding 策略
- 统一空状态（empty state）的布局和图标风格
- 统一左侧边栏（Message tags / Actor list）的样式规范

## Capabilities

### New Capabilities

- `unified-page-layout`: 统一三个视图的 header、内容区、侧边栏的布局和视觉规范

### Modified Capabilities

## Impact

- `vue/src/views/Message.vue` — header 区域样式调整
- `vue/src/views/Media.vue` — header 样式、筛选按钮颜色、内容区宽度调整
- `vue/src/views/Actor.vue` — header 区域样式调整
- 纯前端 CSS/class 变更，不涉及 API 或数据模型
