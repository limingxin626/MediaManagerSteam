## ADDED Requirements

### Requirement: Hashtag 行内高亮
MessageCard 渲染文本时，SHALL 将 `#hashtag` 模式（`#[\w\u4e00-\u9fff]+`）包裹为带有 `hashtag-inline` class 的 `<span>`，使其在视觉上与普通文字区分。

#### Scenario: 文本包含 hashtag
- **WHEN** message text 包含 `#测试` 或 `#hello`
- **THEN** 渲染后的 HTML 中对应文本被包裹为 `<span class="hashtag-inline">#测试</span>`，显示为紫色加粗

#### Scenario: 文本不包含 hashtag
- **WHEN** message text 仅包含普通文字
- **THEN** 渲染结果不受影响

#### Scenario: markdown 标题中的 #
- **WHEN** message text 包含 markdown 标题如 `# 标题`
- **THEN** `#` 被 marked 解析为 `<h1>`，不会被误匹配为 hashtag
