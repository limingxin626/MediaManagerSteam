## ADDED Requirements

### Requirement: 品牌字体引入
系统 SHALL 通过 Google Fonts 加载 Noto Serif SC（标题/强调）和 Noto Sans SC（正文/UI），并定义为 CSS 变量 `--font-display` 和 `--font-body`。字体加载 SHALL 使用 `font-display: swap` 策略，失败时 fallback 到系统字体。

#### Scenario: 正常加载
- **WHEN** 页面首次加载且网络可用
- **THEN** 标题使用 Noto Serif SC，正文使用 Noto Sans SC

#### Scenario: 离线或 CDN 不可用
- **WHEN** Google Fonts CDN 不可达
- **THEN** 界面使用系统默认字体正常显示，无布局错位

### Requirement: 色彩变量体系
`style.css` SHALL 定义三层色彩变量：
- Primary 层：`--color-primary-500/600/700` 品牌主色
- Semantic 层：`--color-success`, `--color-warning`, `--color-danger` 语义色
- Surface 层：现有 `--bg-*`, `--text-*` 变量保留并扩展

组件中的硬编码 Tailwind 色值（如 `indigo-600`, `pink-600`）SHALL 逐步替换为 CSS 变量引用。

#### Scenario: 按钮使用 primary 色
- **WHEN** 渲染主要操作按钮（如 FAB、搜索按钮）
- **THEN** 按钮背景色使用 `--color-primary-600`

#### Scenario: 删除操作使用 danger 色
- **WHEN** 渲染删除按钮或确认弹窗的危险操作按钮
- **THEN** 按钮背景色使用 `--color-danger`

### Requirement: 媒体网格 hover 效果
媒体网格中的每个缩略图在鼠标悬停时 SHALL 显示：轻微放大 `scale(1.05)`、半透明暗色叠层、操作按钮（星标）浮现。过渡 duration 200ms。

#### Scenario: 鼠标悬停在媒体缩略图上
- **WHEN** 用户将鼠标移入网格中某个缩略图
- **THEN** 缩略图放大 5%，显示暗色叠层和操作按钮

#### Scenario: 鼠标移出
- **WHEN** 用户将鼠标移出缩略图
- **THEN** 缩略图恢复原始大小，叠层和按钮淡出

### Requirement: 日期分隔符重设计
消息 feed 中的日期分隔符 SHALL 使用毛玻璃胶囊样式（`backdrop-blur` + 半透明背景 + `rounded-full` pill），并设为 `sticky` 定位（`top: 0`）。

#### Scenario: 滚动消息列表
- **WHEN** 用户滚动消息列表经过日期边界
- **THEN** 日期胶囊固定在滚动区域顶部，直到下一个日期胶囊推走它

### Requirement: 空状态视觉
列表/网格为空时 SHALL 显示 CSS 几何插画 + 提示文字，替代当前的纯文字 "没有消息"。

#### Scenario: 消息列表为空
- **WHEN** 当前筛选条件下无消息
- **THEN** 显示居中的几何插画和 "没有找到消息" 提示文字

#### Scenario: 媒体网格为空
- **WHEN** 媒体列表无内容
- **THEN** 显示居中的几何插画和 "没有找到媒体" 提示文字
