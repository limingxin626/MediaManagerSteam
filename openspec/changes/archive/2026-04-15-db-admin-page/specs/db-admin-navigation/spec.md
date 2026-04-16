## ADDED Requirements

### Requirement: Admin page accessible via sidebar navigation
系统 SHALL 在侧边导航栏中新增管理入口图标，点击后跳转到 `/admin` 路由。

#### Scenario: User clicks admin nav icon
- **WHEN** 用户点击导航栏中的管理图标
- **THEN** 浏览器导航到 `/admin` 页面

#### Scenario: Active state indication
- **WHEN** 用户当前在 `/admin` 页面
- **THEN** 导航栏中的管理图标显示高亮/激活态样式

### Requirement: Admin route is lazily loaded
系统 SHALL 使用路由懒加载加载管理页面组件，不影响主 bundle 体积。

#### Scenario: First visit to admin page
- **WHEN** 用户首次点击管理导航
- **THEN** 系统异步加载管理页面 chunk，加载期间显示 loading 状态

### Requirement: Admin page has tab navigation
系统 SHALL 在管理页面内提供 Tab 切换，包括"概览"和"表浏览"两个 Tab。

#### Scenario: User switches tabs
- **WHEN** 用户点击"表浏览"Tab
- **THEN** 系统切换显示表浏览器视图，"概览"Tab 内容隐藏

#### Scenario: Default tab
- **WHEN** 用户首次进入 `/admin` 页面
- **THEN** 默认显示"概览"Tab
