## MODIFIED Requirements

### Requirement: Video controls and thumbnail strip sync
视频页面的控件（播放/暂停按钮、进度条）与缩略图条 SHALL 同步显示和隐藏。TelegramVideoPlayer SHALL 接受外部传入的 `controlsVisible` 参数作为控件显隐的单一数据源，不再维护内部独立状态。

#### Scenario: Tap video shows both controls and thumbnail strip
- **WHEN** 用户在视频页面单击以显示控件
- **THEN** 视频控件（播放按钮、时间显示、进度条）和缩略图条 SHALL 同时以淡入动画出现

#### Scenario: Controls auto-hide syncs with thumbnail strip
- **WHEN** 视频控件在 3 秒后自动隐藏
- **THEN** 缩略图条 SHALL 同时以淡出动画隐藏

#### Scenario: Tap video hides both controls and thumbnail strip
- **WHEN** 用户在视频页面单击以隐藏控件（控件当前可见时）
- **THEN** 视频控件和缩略图条 SHALL 同时隐藏

#### Scenario: External visibility state drives video controls
- **WHEN** 屏幕级别的 controlsVisible 被外部操作设为 false（如从上一个图片页带过来的隐藏状态）
- **THEN** 视频播放器的控件 SHALL 处于隐藏状态，不自行显示

### Requirement: Thumbnail strip visibility persists across page swipes
缩略图条的显隐状态 SHALL 跨页面滑动保持一致。

#### Scenario: Strip hidden before swipe stays hidden
- **WHEN** 用户在缩略图条隐藏状态下滑动到下一页（无论目标是图片还是视频）
- **THEN** 新页面的缩略图条 SHALL 保持隐藏

#### Scenario: Strip visible before swipe stays visible
- **WHEN** 用户在缩略图条可见状态下滑动到下一页（无论目标是图片还是视频）
- **THEN** 新页面的缩略图条 SHALL 保持可见

#### Scenario: Video controls match strip state after swipe
- **WHEN** 用户从控件隐藏的页面滑动到视频页
- **THEN** 视频页的播放按钮、时间标签 SHALL 处于隐藏状态，仅显示细线进度条
