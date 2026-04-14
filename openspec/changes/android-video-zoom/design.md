## Context

项目 Android 端的 MediaViewerScreen 使用 HorizontalPager 展示图片和视频。图片已通过 `ZoomableImage` 组件实现了完整的缩放体验（双指缩放 1x–5x、双击 2x 切换、拖拽平移）。视频使用 `TelegramVideoPlayer`，目前仅支持水平拖拽快进，不支持缩放。

视频缩放的技术挑战在于手势冲突：同一屏幕区域已有水平 seek 拖拽、播放/暂停点击、HorizontalPager 页面滑动。新增缩放手势需要精确控制事件消费优先级。

## Goals / Non-Goals

**Goals:**
- 视频支持双指缩放（1x–3x）和双击缩放切换
- 缩放状态下支持单指拖拽平移
- 与 HorizontalPager 页面切换正确协调（缩放时禁用翻页）
- 缩放手势与现有 seek 拖拽手势不冲突

**Non-Goals:**
- 不修改视频播放器的 seek、播放/暂停等现有交互
- 不支持视频旋转手势
- 视频最大缩放限制在 3x（视频像素密度低于图片，5x 无意义）

## Decisions

### 1. 在 TelegramVideoPlayer 外层包装缩放层，而非内部改造

**选择**: 在 `TelegramVideoPlayer` 的 `AndroidView(PlayerView)` 外部用 `Box + graphicsLayer` 实现缩放变换。

**理由**:
- 与 ZoomableImage 采用相同的 `graphicsLayer { scaleX/scaleY/translationX/translationY }` 模式
- 不侵入 PlayerView 内部，避免触摸事件路由复杂化
- PlayerView 的内部 seek/tap 手势在缩放后仍可正常工作（坐标自动映射）

**替代方案**: 修改 PlayerView 的 resizeMode + 手势 → 侵入性大，PlayerView 内部事件处理难以精确控制

### 2. 提取通用缩放逻辑为 `ZoomableContainer`

**选择**: 从 `ZoomableImage` 提取缩放状态管理与手势处理为可复用的 `ZoomableContainer` composable，同时用于图片和视频。

**理由**:
- ZoomableImage 的缩放逻辑（Animatable scale/offset、双指检测、双击切换、边界钳制）完全适用于视频
- 避免复制粘贴相同的手势代码
- 统一缩放行为，未来修改只需改一处

**替代方案**: 在 VideoPlayer.kt 中复制 ZoomableImage 的缩放代码 → 维护两份相同逻辑

### 3. 缩放手势优先于 seek 手势

**选择**: 当 scale > 1x 时，单指拖拽执行平移（pan）而非 seek。双指手势始终执行缩放。

**理由**:
- 用户缩放后的直觉是拖拽查看不同区域，不是 seek
- seek 可通过缩放回 1x 后再操作（双击即可回到 1x）
- 避免单指拖拽语义歧义

### 4. 视频缩放范围 1x–3x（区别于图片的 1x–5x）

**选择**: 视频最大缩放 3x。

**理由**: 视频分辨率通常 1080p，3x 缩放已足够查看细节，更高倍率画面模糊无意义。

## Risks / Trade-offs

- **[手势冲突]** 缩放状态下 seek 不可用 → 用户可双击回到 1x 再 seek，行为与图片缩放/翻页逻辑一致
- **[PlayerView 坐标映射]** graphicsLayer 变换后 PlayerView 内部点击区域可能偏移 → 通过 `transformOrigin = TransformOrigin.Center` 和正确的坐标变换处理
- **[性能]** 视频渲染 + 缩放变换可能造成掉帧 → graphicsLayer 仅做 GPU 合成，不重新解码，性能影响极小
