## 1. ZoomableImage 组件

- [x] 1.1 创建 `ZoomableImage.kt` composable，包含 scale（Float）和 offset（Offset）状态，使用 `Animatable` 管理
- [x] 1.2 实现双指缩放手势（`detectTransformGestures`），以双指中心为缩放原点，范围 1x–5x
- [x] 1.3 实现放大状态下单指拖拽平移，计算边界约束防止露出空白
- [x] 1.4 实现双击手势（`detectTapGestures(onDoubleTap)`），1x→2x / >1x→1x 切换，带 spring 动画
- [x] 1.5 实现释放后弹回：scale < 1x 弹回 1x，offset 超出边界弹回边界
- [x] 1.6 添加 `onScaleChanged: (Float) -> Unit` 回调，供外部监听缩放状态

## 2. 集成到 MediaViewerScreen

- [x] 2.1 在 MediaViewerContent 中添加 `currentScale` 状态，通过 `ZoomableImage` 的 `onScaleChanged` 回调更新
- [x] 2.2 将 HorizontalPager 的 `userScrollEnabled` 绑定为 `currentScale <= 1f`
- [x] 2.3 将图片分支的 `AsyncImage` 替换为 `ZoomableImage`，视频分支保持不变
- [x] 2.4 确保切换页面时缩放状态自动重置（页面级 composable 重组即可，因 `beyondViewportPageCount = 0`）

## 3. 验证

- [x] 3.1 在真机上测试图片双指缩放、双击缩放、拖拽平移的手感
- [x] 3.2 验证放大状态下 Pager 不会误翻页，还原后可正常翻页
- [x] 3.3 验证视频页面不受影响，播放控制正常
- [x] 3.4 验证列表模式和浏览模式均工作正常
