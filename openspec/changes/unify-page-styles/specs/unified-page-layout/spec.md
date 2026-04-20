## ADDED Requirements

### Requirement: Header 区域视觉统一
所有页面的 header 区域 SHALL 使用统一的标题字号 `text-lg font-bold`、间距 `py-3`、底部边框 `border-b border-[var(--border-color)]`。

#### Scenario: Message 页面 header
- **WHEN** 用户进入 Message 页面
- **THEN** header 标题显示为 `text-lg font-bold`，间距为 `py-3`

#### Scenario: Media 页面 header
- **WHEN** 用户进入 Media 页面
- **THEN** header 标题显示为 `text-lg font-bold`，间距为 `py-3`

#### Scenario: Actor 页面 header
- **WHEN** 用户进入 Actor 页面
- **THEN** header 标题显示为 `text-lg font-bold`，间距为 `py-3`

### Requirement: 筛选按钮颜色统一
所有页面的筛选/过滤按钮激活态 SHALL 使用 `bg-[var(--color-primary-600)] text-white`，不得使用硬编码颜色。

#### Scenario: Media 页面类型筛选按钮
- **WHEN** 用户在 Media 页面点击类型筛选按钮（全部/视频/图片）
- **THEN** 激活按钮使用 `bg-[var(--color-primary-600)] text-white`，而非 `bg-pink-600`

### Requirement: 空状态布局统一
所有页面的空状态 SHALL 使用居中 flex 布局，包含图标和提示文字，风格一致。

#### Scenario: 空状态显示
- **WHEN** 任意页面无内容可展示
- **THEN** 显示居中的空状态提示，图标和文字样式在三个页面间保持一致
