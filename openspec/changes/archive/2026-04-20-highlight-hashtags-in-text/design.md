## Context

MessageCard 使用 `marked` 将 message text 渲染为 HTML。文本中的 `#hashtag` 模式（正则 `#[\w\u4e00-\u9fff]+`）目前在渲染后只是普通文本，没有视觉区分。现有的 `tag-chip` 样式用于底部标签展示，但行内 hashtag 需要更轻量的行内样式。

## Goals / Non-Goals

**Goals:**
- 在 `renderedText` 输出中将 `#hashtag` 包裹为带样式的 `<span>`，使其颜色醒目
- 样式与 `tag-chip` 风格呼应（紫色/indigo 色系），但不用 pill 形式，保持行内阅读体验

**Non-Goals:**
- 不做 hashtag 点击交互（如点击筛选）
- 不改变后端 tag 解析逻辑

## Decisions

1. **在 marked 渲染后做正则替换**：先让 marked 解析 markdown，再对 HTML 结果中非标签内的 `#hashtag` 做替换。这样避免干扰 markdown 解析。使用负向断言排除 HTML 标签属性中的误匹配。

2. **使用 CSS class `hashtag-inline`**：在 `style.css` 中定义行内 hashtag 样式，颜色使用 indigo/紫色系，加粗，与暗色模式兼容。

## Risks / Trade-offs

- [正则可能误匹配 HTML 属性中的 # 字符] → 使用负向断言 `(?<!["=])` 排除
