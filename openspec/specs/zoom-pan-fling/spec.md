### Requirement: Fling momentum after pan release
放大状态下（scale > 1x）单指拖拽松手后，平移 SHALL 以手指离开时的速度继续滑动，并以自然衰减曲线减速直至停止。

#### Scenario: Fast swipe creates fling
- **WHEN** 用户在放大状态下快速拖拽后松手，且松手时速度 > 0
- **THEN** 媒体 SHALL 沿松手方向继续滑动，速度逐渐衰减至零

#### Scenario: Slow drag has minimal fling
- **WHEN** 用户在放大状态下缓慢拖拽后松手
- **THEN** 媒体 SHALL 几乎立即停止（衰减动画极短），不产生明显的额外位移

#### Scenario: Fling stops at boundary
- **WHEN** fling 动画过程中媒体到达平移边界（媒体边缘与屏幕边缘对齐）
- **THEN** fling 动画 SHALL 立即停止，不产生回弹或穿越边界

#### Scenario: Fling respects axis-independent bounds
- **WHEN** fling 过程中媒体在水平方向到达边界但垂直方向未到达
- **THEN** 水平方向 SHALL 停止移动，垂直方向 SHALL 继续衰减

### Requirement: Fling applies to both image and video zoom
图片（ZoomableContainer）和视频（TelegramVideoPlayer）的放大拖拽 SHALL 都支持 fling 惯性。

#### Scenario: Image zoom pan has fling
- **WHEN** 用户在放大的图片上快速拖拽后松手
- **THEN** 图片 SHALL 产生 fling 惯性滑动

#### Scenario: Video zoom pan has fling
- **WHEN** 用户在放大的视频上快速拖拽后松手
- **THEN** 视频 SHALL 产生 fling 惯性滑动
