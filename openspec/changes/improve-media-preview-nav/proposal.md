## Why

MediaPreview 弹层用于在 Message Feed 等场景下浏览一组媒体。当前实现有两个体验问题：切换上一/下一张时，底部缩略图条不会把当前项滚动到中间，长列表中很快就看不到自己在哪；主图切换是瞬时替换，缺少方向感和过渡，让人感觉生硬。修复这两点能让浏览体验更接近常见的相册/Lightbox 应用。

## What Changes

- 切换 `currentIndex` 时，底部缩略图条 SHALL 把当前缩略图水平居中显示，而不是仅 `nearest`。
- 缩略图条容器布局调整：当总宽度不足时居中显示；超出后允许水平滚动并以当前项居中。
- 主图（图片 / 视频）切换时 SHALL 有滑动方向感的进入/退出过渡（向前 → 从右进入、向左退出；向后反向）。
- 过渡 SHALL 与现有 UI motion system 一致（短促、缓动平滑），不阻塞键盘连续翻页。

## Capabilities

### New Capabilities
- `media-preview-navigation`: 覆盖 MediaPreview 弹层的多媒体导航交互——缩略图条居中跟随、主图切换过渡。

### Modified Capabilities
<!-- none -->

## Impact

- 代码：`vue/src/components/MediaPreview.vue`（模板：缩略图条布局；脚本：滚动逻辑；样式：transition class）。
- 无后端、无 API、无数据库变更。
- 不影响 MediaDetail 全屏页（由 `media-viewer-controls-sync` 管辖），仅影响弹层 MediaPreview。
