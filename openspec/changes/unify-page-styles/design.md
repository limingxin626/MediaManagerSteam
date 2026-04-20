## Context

三个主页面（Message、Media、Actor）在独立迭代中产生了视觉差异。当前状态：

| 属性 | Message | Media | Actor |
|------|---------|-------|-------|
| 标题字号 | text-base | text-xl | text-2xl |
| Header 间距 | py-2 | py-3 | py-4 |
| 筛选按钮颜色 | CSS 变量 | 硬编码 pink-600 | CSS 变量 |
| 内容区宽度 | max-w-3xl | max-w-4xl | max-w-2xl |

## Goals / Non-Goals

**Goals:**
- 统一 header 区域的视觉规范（字号、间距、边框）
- 统一筛选按钮颜色为 CSS 变量
- 统一内容区 max-width 策略
- 统一空状态布局

**Non-Goals:**
- 不重构页面布局结构（三栏 vs 单栏保持现状）
- 不提取共享组件（如 PageHeader），只统一 class
- 不修改功能逻辑

## Decisions

1. **Header 标题统一为 `text-lg font-bold`**：在 base/xl/2xl 之间取中间值，适合所有页面
2. **Header 间距统一为 `py-3`**：三个值的中间值
3. **筛选按钮统一使用 `bg-[var(--color-primary-600)]`**：与项目已有的 primary 色彩体系一致
4. **内容区宽度**：feed 类页面（Message/Actor）统一 `max-w-3xl`，grid 类页面（Media）保持 `max-w-4xl`（grid 需要更宽空间）
5. **只改 class，不提取组件**：变更最小化，避免引入新抽象

## Risks / Trade-offs

- [视觉回归] → 变更仅涉及 Tailwind class，可通过浏览器快速验证
- [Media 页 max-width 不同] → grid 布局确实需要更宽空间，这是合理的差异而非不一致
