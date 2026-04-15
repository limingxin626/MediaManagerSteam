### Requirement: Image single-tap toggles thumbnail strip
在图片页面，单击 SHALL 切换缩略图条（MediaStripBar）的显示与隐藏。

#### Scenario: Tap image to hide thumbnail strip
- **WHEN** 用户在图片页面单击，且缩略图条当前可见
- **THEN** 缩略图条 SHALL 以淡出动画隐藏

#### Scenario: Tap image to show thumbnail strip
- **WHEN** 用户在图片页面单击，且缩略图条当前隐藏
- **THEN** 缩略图条 SHALL 以淡入动画显示

### Requirement: Video controls and thumbnail strip sync
视频页面的控件（播放/暂停按钮、进度条）与缩略图条 SHALL 同步显示和隐藏。

#### Scenario: Tap video shows both controls and thumbnail strip
- **WHEN** 用户在视频页面单击以显示控件
- **THEN** 视频控件（播放按钮、时间显示、进度条）和缩略图条 SHALL 同时以淡入动画出现

#### Scenario: Controls auto-hide syncs with thumbnail strip
- **WHEN** 视频控件在 3 秒后自动隐藏
- **THEN** 缩略图条 SHALL 同时以淡出动画隐藏

#### Scenario: Tap video hides both controls and thumbnail strip
- **WHEN** 用户在视频页面单击以隐藏控件（控件当前可见时）
- **THEN** 视频控件和缩略图条 SHALL 同时隐藏

### Requirement: Thumbnail strip visibility persists across page swipes
缩略图条的显隐状态 SHALL 跨页面滑动保持一致。

#### Scenario: Strip hidden before swipe stays hidden
- **WHEN** 用户在缩略图条隐藏状态下滑动到下一页
- **THEN** 新页面的缩略图条 SHALL 保持隐藏

#### Scenario: Strip visible before swipe stays visible
- **WHEN** 用户在缩略图条可见状态下滑动到下一页
- **THEN** 新页面的缩略图条 SHALL 保持可见
