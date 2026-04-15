## Context

MediaViewerScreen 是全屏媒体预览器，使用 HorizontalPager 展示图片和视频列表。当前缩放/平移由 `ZoomableContainer` 统一处理，边界计算基于容器尺寸（`containerSize`），未考虑媒体实际宽高比。缩略图条（`MediaStripBar`）始终可见，与视频控件的显隐无关联。

**当前问题：**
1. `calculateBounds` 用 `containerSize` 计算边界，但当媒体未填满容器时（如横向视频在竖屏中），允许在未填满方向上平移，导致媒体偏离中心
2. 平移边界基于容器而非媒体可见区域，放大后拖拽可露出媒体外的空白
3. 缩略图条与视频控件独立管理，无同步机制

## Goals / Non-Goals

**Goals:**
- 媒体在未填满方向上始终居中，不允许在该方向平移
- 放大后平移边界精确对齐媒体实际边缘，不露出空白
- 图片单击切换缩略图条显隐
- 视频控件与缩略图条同步显隐

**Non-Goals:**
- 不修改缩放范围（图片 5x，视频 3x）
- 不修改双击缩放倍率（2x）
- 不修改 HorizontalPager 的手势协调逻辑
- 不添加新动画或过渡效果

## Decisions

### 1. 在 ZoomableContainer 中引入 mediaAspectRatio 参数

**决策**：为 `ZoomableContainer` 添加 `mediaAspectRatio: Float?` 参数，用于计算媒体在容器内的实际可见区域。

**依据**：在 `ContentScale.Fit` 模式下，媒体按比例缩放以适配容器，可能在某一方向留白。通过 aspect ratio 可以精确计算媒体的实际渲染尺寸：
```
if (mediaAR > containerAR):  // 横向媒体，上下留白
    mediaWidth = containerWidth
    mediaHeight = containerWidth / mediaAR
else:  // 竖向媒体，左右留白
    mediaHeight = containerHeight
    mediaWidth = containerHeight * mediaAR
```

**替代方案**：传入媒体原始宽高像素值 — 但 aspect ratio 更简洁，且避免了像素/dp 转换。

### 2. 基于媒体可见区域重新计算平移边界

**决策**：`calculateBounds` 改为基于媒体实际渲染尺寸（而非容器尺寸）计算边界。在媒体未填满的方向上，将最大偏移限制为使媒体边缘不超过容器边缘：

```
scaledMediaWidth = mediaWidth * scale
scaledMediaHeight = mediaHeight * scale

// 水平方向
if (scaledMediaWidth <= containerWidth):
    maxX = 0  // 居中锁定
else:
    maxX = (scaledMediaWidth - containerWidth) / 2

// 垂直方向同理
```

**依据**：这确保了：
- 未填满方向：offset 锁定为 0（媒体始终居中）
- 已超出方向：平移范围恰好到媒体边缘与屏幕边缘对齐

### 3. 控件显隐同步架构 — 状态提升到 MediaViewerScreen

**决策**：在 `MediaViewerScreen` 中维护一个 `controlsVisible` 状态，通过回调传递给 `TelegramVideoPlayer` 和 `MediaStripBar`：
- 图片页面：`ZoomableContainer.onSingleTap` 切换 `controlsVisible`，控制 `MediaStripBar` 显隐
- 视频页面：`TelegramVideoPlayer` 的 `toggleControls` 通过回调通知 `MediaViewerScreen` 同步缩略图条显隐

**替代方案**：在 `VideoPlayer` 内部直接控制缩略图条 — 但这违反组合原则，缩略图条属于 `MediaViewerScreen` 的职责。

### 4. 图片单击行为变更

**决策**：图片页面的 `onSingleTap` 从无操作改为切换缩略图条显隐（与视频控件行为对齐）。

**依据**：用户对图片和视频预期一致的交互模式 — 单击切换 UI 元素。

## Risks / Trade-offs

- **[不同媒体源的 aspect ratio 获取]** → 图片通过 Coil 加载后可获得 intrinsic size；视频通过 ExoPlayer 的 `videoSize` 回调获取。在数据加载完成前使用 `null` 退化为当前行为。
- **[视频控件自动隐藏与缩略图条同步]** → 视频控件 3 秒后自动隐藏，缩略图条须跟随。通过回调机制在 `controlsVisible` 变化时同步更新。
- **[性能影响]** → 边界计算增加一次宽高比判断，开销可忽略。
