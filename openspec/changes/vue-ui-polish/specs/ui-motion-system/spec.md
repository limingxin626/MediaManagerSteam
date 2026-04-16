## ADDED Requirements

### Requirement: 列表项进场动画
MessageCard 进入视口时 SHALL 播放 fade-up 进场动画（opacity 0→1, translateY 8px→0, duration 300ms）。同一批次内的多个卡片 SHALL 通过 animation-delay 产生 stagger 效果（每项延迟 50ms）。

#### Scenario: 首次加载消息列表
- **WHEN** 消息列表首次渲染，卡片进入视口
- **THEN** 每张卡片依次以 fade-up 动画出现，间隔 50ms

#### Scenario: 滚动加载更多消息
- **WHEN** 用户向上滚动触发加载更多，新卡片 prepend 到列表
- **THEN** 新卡片以 fade-up 动画进场

#### Scenario: 用户偏好减少动画
- **WHEN** 系统设置了 `prefers-reduced-motion: reduce`
- **THEN** 所有进场动画 SHALL 被跳过，卡片直接显示

### Requirement: 星标 toggle 微动效
点击星标按钮时 SHALL 播放 scale bounce 动画（scale 1→1.3→1, duration 300ms, ease-out）。

#### Scenario: 收藏一条消息
- **WHEN** 用户点击消息卡片的星标按钮
- **THEN** 星标图标播放 bounce 动画并变为黄色

#### Scenario: 取消收藏
- **WHEN** 用户点击已收藏的星标按钮
- **THEN** 星标图标播放 bounce 动画并恢复为默认色

### Requirement: 详情面板滑入动画
Message 视图右侧详情面板打开时 SHALL 从右侧滑入（translateX 100%→0, opacity 0→1, duration 250ms）。关闭时 SHALL 反向滑出。

#### Scenario: 打开消息详情
- **WHEN** 用户点击 MessageCard 的展开箭头
- **THEN** 右侧详情面板从右侧滑入显示

#### Scenario: 关闭消息详情
- **WHEN** 用户关闭详情面板
- **THEN** 面板向右滑出消失

### Requirement: 路由切换过渡
页面路由切换时 SHALL 有 fade + translateY 过渡动画（duration 200ms）。过渡 SHALL 与 keep-alive 缓存兼容。

#### Scenario: 从消息页切换到媒体页
- **WHEN** 用户点击导航切换到媒体页
- **THEN** 页面内容以 fade-down 动画切换

### Requirement: 按钮 press 状态反馈
所有可点击按钮在按下时 SHALL 有 `scale(0.96)` 缩小反馈。

#### Scenario: 用户按下按钮
- **WHEN** 用户按下（mousedown/touchstart）任意按钮
- **THEN** 按钮缩小至 96% 大小
- **WHEN** 用户释放按钮
- **THEN** 按钮恢复原始大小
