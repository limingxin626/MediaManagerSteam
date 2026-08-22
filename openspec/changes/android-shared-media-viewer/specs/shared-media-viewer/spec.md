## ADDED Requirements

### Requirement: Shared source-neutral viewer

Android SHALL 使用不依赖 Room 或 MediaStore 的共享预览 UI 渲染两种媒体来源。

#### Scenario: 预览 Room 媒体
- **WHEN** 用户从原 Room 媒体入口打开预览
- **THEN** 页面保持现有窗口加载、左右浏览和收藏行为

#### Scenario: 预览系统媒体
- **WHEN** 用户从 MediaStore 媒体页打开预览
- **THEN** 页面使用与 Room 媒体相同的预览布局和手势
- **AND** 不插入或更新 Room，不上传媒体

### Requirement: Complete image interaction

共享预览 SHALL 支持图片双击缩放、双指缩放、缩放后拖动和回弹，并在图片放大时避免 pager 抢占拖动手势。

#### Scenario: 放大系统图片
- **WHEN** 用户双击或双指缩放系统图片
- **THEN** 图片按现有 `ZoomableImage` 行为缩放和平移

### Requirement: Complete video interaction

共享预览 SHALL 使用现有视频播放器提供播放暂停、进度、seek 和视频缩放控制，并只让当前页视频自动播放。

#### Scenario: 滑离视频
- **WHEN** 用户从视频页滑到相邻媒体
- **THEN** 离开的播放器不继续自动播放

### Requirement: Pager, counter, and thumbnail strip

共享预览 SHALL 提供左右分页、当前位置/总数页码和可点击的底部缩略图条，缩略图条 SHALL 跟随当前页居中。

#### Scenario: 点击缩略图
- **WHEN** 用户点击非当前项缩略图
- **THEN** pager 平滑滚动到对应媒体

### Requirement: Source-specific actions

共享预览 SHALL 仅在数据源提供收藏操作时显示收藏按钮。

#### Scenario: 系统媒体预览未提供操作
- **WHEN** MediaStore adapter 未提供收藏回调
- **THEN** 不显示收藏按钮

#### Scenario: 系统媒体提供本机元数据操作
- **WHEN** MediaStore adapter 提供独立的本机 metadata 收藏回调
- **THEN** 共享 viewer 显示收藏按钮并仅调用该回调
- **AND** 不提供上传、删除或文件编辑操作
