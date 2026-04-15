## Context

MediaViewerScreen 是一个全屏 Telegram 风格媒体预览器，支持图片和视频的左右滑动切换。当前实现存在三个 bug：

1. **控件显隐跨页不持续**：`MediaViewerContent` 持有一个 `controlsVisible` 状态，但 `TelegramVideoPlayer` 内部有独立的 `controlsVisible`（初始 = false）。当用户在图片页隐藏控件后切到视频页，视频内部的 `onControlsVisibilityChanged` 回调不会立即触发（因为视频的 `controlsVisible` 初始就是 false），所以屏幕级状态保持 false（正确）。但当切到下一个图片页时，没有人修改 `controlsVisible`，它保持刚才的值。问题在于视频组件的 autoPlay 触发、ExoPlayer listener 等路径可能会间接影响回调，导致状态反复。

2. **视频控件无法隐藏**：同步是单向的——视频通过 `onControlsVisibilityChanged` 回调通知屏幕，但屏幕无法告诉视频"请隐藏控件"。当用户在图片页隐藏了 `controlsVisible`，然后切到视频页，视频内部的 `controlsVisible` 在没有外部信号的情况下可能独立触发显示。

3. **拖拽无惯性**：`ZoomableContainer` 和 `TelegramVideoPlayer` 的放大拖拽都使用 `offset.snapTo()`，手指离开后立即停止。

## Goals / Non-Goals

**Goals:**
- 控件显隐状态在所有页面类型（图片/视频）间保持一致
- 视频组件接受外部控制的显隐状态，实现双向同步
- 放大拖拽松手后有速度衰减惯性（fling），在边界处自然停止
- 保持现有交互模式不变（单击切换、双击缩放、3 秒自动隐藏）

**Non-Goals:**
- 不修改视频的自动隐藏时长（保持 3 秒）
- 不添加边缘回弹效果（overscroll bounce）
- 不重构 ZoomableContainer 的整体架构
- 不修改非缩放模式下的视频交互

## Decisions

### Decision 1: TelegramVideoPlayer 接受外部 controlsVisible 参数

**方案**：将 `TelegramVideoPlayer` 的 `controlsVisible` 从内部 `remember` 状态改为接受外部传入参数 + 回调的受控模式（controlled component pattern）。

新签名增加 `controlsVisible: Boolean` 参数，组件内部不再持有自己的 `controlsVisible` 状态，而是直接使用外部传入的值。所有切换操作通过 `onControlsVisibilityChanged` 回调请求外部变更。

**理由**：这是 Compose 标准的状态提升模式（state hoisting），确保单一数据源。替代方案是用 `LaunchedEffect` 监听外部状态变化并同步到内部状态，但这容易产生竞态条件和不一致。

### Decision 2: 页面切换时不重置 controlsVisible

**方案**：在 `LaunchedEffect(pagerState.settledPage)` 中仅重置 `currentScale`，不修改 `controlsVisible`。这样用户在某一页设置的显隐状态自然保持到下一页。

**理由**：这是最简单的修复——问题不是"切换时重置"，而是视频组件的独立状态导致不一致。修复视频的状态管理后，`controlsVisible` 自然保持。

### Decision 3: Fling 使用 Compose 的 `animateDecay` + `splineBasedDecay`

**方案**：在手势结束时，记录最后几帧的速度（使用 `VelocityTracker`），然后用 `animateDecay(velocity, splineBasedDecay)` 启动衰减动画。动画过程中持续 `clampOffset` 确保不超出边界。

**理由**：
- `splineBasedDecay` 是 Android 平台原生的 fling 衰减曲线，与系统滚动行为一致
- 替代方案 `exponentialDecay` 在低速时感觉太快停止
- `VelocityTracker` 是 Compose 标准的速度追踪工具，比手算更精确

### Decision 4: ZoomableContainer 和 TelegramVideoPlayer 的 fling 实现统一

**方案**：两处的放大拖拽代码结构相同（`awaitEachGesture` + 单指 pan），分别在各自代码中添加相同的 fling 逻辑，而非提取共享工具函数。

**理由**：虽然代码有重复，但两个组件的参数（maxScale、边界计算）和上下文不同，强行抽象反而增加耦合。保持简单、各自完整。

## Risks / Trade-offs

- **Fling 动画与边界 clamp 的交互**：fling 动画中每帧都需要 clamp，到达边界时应立即停止而非反弹。→ 使用 `animateDecay` 的 `block` 回调在每帧检查边界，超出时取消动画。
- **VelocityTracker 精度**：在高刷新率屏幕上 pointer event 频率高，速度计算可能波动。→ `VelocityTracker` 内部已做平滑处理，无需额外处理。
- **视频 controlsVisible 改为外部控制后，autoHide 的 Job 管理**：3 秒自动隐藏的 `hideControlsJob` 现在调用回调而非直接修改状态。→ 保持 Job 逻辑不变，只是 `scheduleHideControls` 中通过回调通知外部。
