## MODIFIED Requirements

### Requirement: Pan when zoomed
放大状态下（scale > 1x），媒体 SHALL 支持单指拖拽平移。平移边界 SHALL 基于媒体实际渲染尺寸（而非容器尺寸）计算。当媒体在某一方向上的缩放后尺寸未超过容器该方向的尺寸时，该方向的 offset SHALL 锁定为 0（媒体居中）。

#### Scenario: User drags image while zoomed in
- **WHEN** 用户在 scale > 1x 时单指拖拽
- **THEN** 图片随手指平移

#### Scenario: Pan is bounded to media edges (not container edges)
- **WHEN** 用户在放大状态下拖拽媒体
- **THEN** 平移 SHALL 限制为媒体边缘不离开屏幕对应边缘。例如向右上方拖拽时，最多拖到媒体左边缘与屏幕左边缘对齐、媒体下边缘与屏幕下边缘对齐。不 SHALL 出现媒体内容以外的空白。

#### Scenario: Media stays centered on unfilled axis
- **WHEN** 媒体未填满容器某一方向（如竖屏下的横向视频，上下边已抵达屏幕但左右有留白）
- **THEN** 在放大过程中，只要该方向上缩放后的媒体尺寸仍未超过容器尺寸，媒体 SHALL 在该方向上保持居中，offset 锁定为 0

#### Scenario: Axis unlocks when media exceeds container
- **WHEN** 媒体在某一方向上的缩放后尺寸超过容器该方向的尺寸
- **THEN** 该方向 SHALL 允许平移，平移范围为 `±(scaledMediaDim - containerDim) / 2`

#### Scenario: Offset resets when returning to 1x
- **WHEN** scale 回到 1x（通过双击还原或缩放回 1x）
- **THEN** offset SHALL 重置为 (0, 0)
