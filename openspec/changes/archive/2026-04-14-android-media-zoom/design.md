## Context

MediaViewerScreen 是全屏媒体查看器，使用 HorizontalPager 实现左右滑动切换。当前图片用 Coil 的 `AsyncImage` 以 `ContentScale.Fit` 渲染，没有任何手势交互。视频使用自定义 `TelegramVideoPlayer`（ExoPlayer），已有点击控制和滑动 seek。

核心挑战：在 HorizontalPager 内部添加图片缩放手势，需要处理手势冲突 —— 放大时平移 vs 未放大时翻页。

## Goals / Non-Goals

**Goals:**
- 图片支持双指缩放（pinch-to-zoom），范围 1x–5x
- 图片支持双击切换放大/还原（2x ↔ 1x），带平滑动画
- 放大状态下支持单指拖拽平移（pan），并限制在图片边界内
- 放大状态下阻止 Pager 拦截水平手势，还原后恢复翻页
- 状态仅限当前页面，切换页后自动重置为 1x

**Non-Goals:**
- 视频页面的缩放（视频有自己的手势交互）
- 图片旋转手势
- 持久化缩放状态
- GIF 动图的特殊处理（当静态图片处理即可）

## Decisions

### 1. 纯 Compose 手势实现 vs 第三方库

**选择：纯 Compose `pointerInput` 手势**

理由：
- `detectTransformGestures` 提供 pan/zoom/rotation 回调，满足需求
- `detectTapGestures(onDoubleTap)` 处理双击
- 无需引入新依赖，项目已使用 Compose Foundation
- 第三方库（如 `net.engawapg.lib:zoomable`）增加依赖且可能与 Pager 手势冲突难以调试

### 2. 手势冲突解决策略

**选择：通过 `HorizontalPager` 的 `userScrollEnabled` 动态控制**

方案：
- 将 zoom scale 作为状态提升到 Pager 所在层级
- `userScrollEnabled = (currentScale <= 1f)` —— 放大时禁止 Pager 滑动
- 平移到图片边界时不恢复 Pager 滑动（避免误触）

替代方案考虑：
- `NestedScrollConnection` —— 过于复杂，且 Pager 的手势拦截发生在 parent 层，子 composable 难以可靠消费
- 自定义 `PointerInputScope` 消费事件 —— 需要深度理解 Compose 触摸分发，维护成本高

### 3. 组件封装

**选择：创建独立 `ZoomableImage` composable**

理由：
- 将缩放逻辑（scale/offset 状态 + 手势处理）封装在一个组件中
- MediaViewerScreen 只需将 `AsyncImage` 替换为 `ZoomableImage`
- 通过 `onScaleChanged: (Float) -> Unit` 回调通知 Pager 当前缩放比例

### 4. 缩放动画

**选择：使用 `Animatable` 配合 `animateTo`**

- 双击缩放用 `spring` 动画（naturalFeel）
- 释放后 scale < 1f 时弹回 1f（使用 `spring`）
- 释放后 offset 超出边界时弹回边界

## Risks / Trade-offs

- **[手指数检测精度]** → 双指缩放中偶尔触发双击。Mitigation: 双击回调中检查当前是否正在进行 transform 手势，是则忽略。
- **[Pager 重组性能]** → `userScrollEnabled` 变化会触发 Pager 重组。Mitigation: 仅在 scale 跨越 1.0 阈值时切换，避免频繁重组。
- **[大图内存]** → 放大到 5x 不会改变实际纹理分辨率（Coil 已加载完整图），仅是渲染变换，无额外内存开销。
