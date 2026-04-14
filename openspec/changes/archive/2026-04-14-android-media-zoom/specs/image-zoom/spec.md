## ADDED Requirements

### Requirement: Pinch-to-zoom on images
在 MediaViewerScreen 中，图片页面 SHALL 支持双指缩放手势。缩放范围 SHALL 为 1x（原始大小）到 5x。缩放 SHALL 以双指中心点为原点。

#### Scenario: User pinches outward to zoom in
- **WHEN** 用户在图片上向外张开双指
- **THEN** 图片以双指中心为原点放大，最大不超过 5x

#### Scenario: User pinches inward to zoom out
- **WHEN** 用户在放大状态下向内合拢双指
- **THEN** 图片缩小，最小不低于 1x

#### Scenario: Scale snaps back when released below 1x
- **WHEN** 用户缩放时 scale 低于 1x 后松手
- **THEN** 图片 SHALL 以弹簧动画回弹到 1x

### Requirement: Double-tap to toggle zoom
图片 SHALL 支持双击手势在放大和还原之间切换。

#### Scenario: Double-tap to zoom in from 1x
- **WHEN** 用户在 scale = 1x 时双击图片
- **THEN** 图片 SHALL 以双击位置为中心，带动画放大到 2x

#### Scenario: Double-tap to reset from zoomed state
- **WHEN** 用户在 scale > 1x 时双击图片
- **THEN** 图片 SHALL 带动画还原到 1x，offset 重置为 (0, 0)

### Requirement: Pan when zoomed
放大状态下（scale > 1x），图片 SHALL 支持单指拖拽平移，以查看放大后不在视口内的区域。

#### Scenario: User drags image while zoomed in
- **WHEN** 用户在 scale > 1x 时单指拖拽
- **THEN** 图片随手指平移

#### Scenario: Pan is bounded to image edges
- **WHEN** 用户平移到图片内容的边缘
- **THEN** 平移 SHALL 停止，不露出图片外的空白区域

#### Scenario: Offset resets when returning to 1x
- **WHEN** scale 回到 1x（通过双击还原或缩放回 1x）
- **THEN** offset SHALL 重置为 (0, 0)

### Requirement: Pager gesture coordination
放大状态下 SHALL 阻止 HorizontalPager 拦截水平滑动手势，避免误翻页。

#### Scenario: Pager swipe disabled when zoomed
- **WHEN** 当前图片 scale > 1x
- **THEN** HorizontalPager 的左右翻页手势 SHALL 被禁用

#### Scenario: Pager swipe re-enabled when zoom reset
- **WHEN** 当前图片 scale 回到 1x
- **THEN** HorizontalPager 的左右翻页手势 SHALL 恢复正常

### Requirement: Zoom state is page-scoped
每页的缩放状态 SHALL 独立于其他页面，切换页后不应保留前一页的缩放。

#### Scenario: Switching pages resets zoom
- **WHEN** 用户从一个放大的图片页滑到（或点击缩略图跳到）另一页
- **THEN** 新页面 SHALL 以 scale = 1x, offset = (0, 0) 显示

### Requirement: Video pages unaffected
视频页面 SHALL NOT 受缩放功能影响，保持现有的 TelegramVideoPlayer 交互行为。

#### Scenario: Video page has no zoom gesture
- **WHEN** 用户在视频页面进行双指或双击手势
- **THEN** 视频播放器 SHALL 保持其现有行为（点击显示/隐藏控制栏、滑动 seek），不触发缩放
