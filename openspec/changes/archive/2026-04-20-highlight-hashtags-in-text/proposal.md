## Why

MessageCard 中 `#hashtag` 文本在渲染后与普通文字没有视觉区分，用户很难一眼识别标签。需要在文本中对 `#hashtag` 加上醒目的样式，使其在视觉上与周围文字区分开来。

## What Changes

- 在 `renderedText` 计算属性中，将 `#hashtag` 模式替换为带有特殊样式的 `<span>` 标签
- 在 CSS 中添加行内 hashtag 高亮样式，与现有 `tag-chip` 风格呼应但更适合行内文本

## Capabilities

### New Capabilities
- `hashtag-highlight`: 在 MessageCard 渲染文本中高亮 `#hashtag`，使用行内彩色样式

### Modified Capabilities

## Impact

- `vue/src/components/MessageCard.vue` — `renderedText` computed 属性
- `vue/src/style.css` — 新增行内 hashtag 样式
