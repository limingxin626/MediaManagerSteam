## 1. 修复视频控件双向同步

- [x] 1.1 修改 `TelegramVideoPlayer` 签名：添加 `controlsVisible: Boolean` 参数，移除内部 `var controlsVisible by remember`，改为直接使用外部传入值
- [x] 1.2 修改 `TelegramVideoPlayer` 内部的 `toggleControls()` 和 `scheduleHideControls()`：不再直接修改内部状态，而是通过 `onControlsVisibilityChanged` 回调请求外部变更
- [x] 1.3 更新 `MediaViewerContent` 中调用 `TelegramVideoPlayer` 的位置：传入 `controlsVisible` 参数，并在 `onControlsVisibilityChanged` 回调中更新屏幕级状态

## 2. 修复控件显隐跨页持续性

- [x] 2.1 确认 `LaunchedEffect(pagerState.settledPage)` 中不会重置 `controlsVisible`（当前只重置 `currentScale`，已正确）
- [x] 2.2 验证 ZoomableImage 的 `onSingleTap` 仍然正确切换 `controlsVisible`，且切换后状态在翻页时保持

## 3. 添加 Fling 惯性 — ZoomableContainer

- [x] 3.1 在 `ZoomableContainer` 的手势处理中引入 `VelocityTracker`，在每帧 pan 时调用 `addPosition` 追踪速度
- [x] 3.2 在手势结束（`activePointers.isEmpty()` 且 `didTransform`）时，取得 `VelocityTracker.calculateVelocity()`，使用 `animateDecay(velocity, splineBasedDecay)` 启动惯性动画
- [x] 3.3 Fling 动画中每帧调用 `clampOffset`，若 offset 被 clamp（到达边界）则对该轴的速度归零或停止动画

## 4. 添加 Fling 惯性 — TelegramVideoPlayer

- [x] 4.1 在 `TelegramVideoPlayer` 的缩放手势处理中引入 `VelocityTracker` 和速度追踪
- [x] 4.2 在手势结束时启动 `animateDecay` 惯性动画，逻辑与 ZoomableContainer 相同
- [x] 4.3 Fling 动画中的边界 clamp 处理

## 5. 集成验证

- [x] 5.1 测试：图片页隐藏控件 → 滑动到视频页 → 控件保持隐藏
- [x] 5.2 测试：视频页显示控件 → 滑动到图片页 → 控件保持显示
- [x] 5.3 测试：视频页单击切换控件 → 3 秒自动隐藏 → 缩略图条同步
- [x] 5.4 测试：放大图片/视频后快速拖拽松手 → 有惯性滑动 → 边界处停止
