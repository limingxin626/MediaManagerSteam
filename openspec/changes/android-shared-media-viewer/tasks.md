## 1. 共享预览模型与组件

- [x] 1.1 新增 `ViewerMediaItem` 及 Room `Media`、`SystemMedia` 映射
- [x] 1.2 从 `MediaViewerScreen` 抽取共享全屏 viewer，保留 pager、控制栏和页码
- [x] 1.3 抽取通用缩略图条并支持当前项居中与点击跳转
- [x] 1.4 接入 `ZoomableImage` 与 `TelegramVideoPlayer`，保持缩放时 pager 手势协调

## 2. Room 预览适配

- [x] 2.1 将 Room `MediaViewerScreen` 的各加载模式映射到共享 viewer
- [x] 2.2 保留窗口前后扩展、跨消息加载和收藏写入行为
- [ ] 2.3 验证 Room 预览外观和交互无回归

## 3. 系统媒体预览适配

- [x] 3.1 将 `SystemMediaDetailScreen` 改为共享 viewer adapter
- [x] 3.2 支持列表为空时按 content URI 加载单项 fallback
- [x] 3.3 禁用系统媒体收藏和所有 Room/上传写操作

## 4. 验证

- [x] 4.1 添加中立模型映射测试
- [x] 4.2 运行 `testDebugUnitTest` 与 `assembleDebug`
- [ ] 4.3 验证系统图片缩放、视频控制、左右滑动、页码和缩略图跳转
- [ ] 4.4 验证 Room 预览收藏与窗口加载没有回归
