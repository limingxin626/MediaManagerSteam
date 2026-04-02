# 媒体查看器 Telegram 风格改造

日期：2026-03-31

## 功能概述

将全屏媒体查看器（`MediaViewerScreen`）改造为 Telegram 风格，包含以下三个主要功能：

1. **共享元素过渡动画**：缩略图展开为全屏，关闭时收缩回原位
2. **Telegram 风格视频播放器**：永久进度条 + 点击显示控件（不变灰）
3. **底部横向缩略图导航条**：显示当前消息的所有媒体，支持点击跳转

---

## 一、共享元素过渡动画

### 实现方案

使用 Compose `SharedTransitionLayout`（`@ExperimentalSharedTransitionApi`，BOM 2024.09.00 / Compose 1.7.5）。

**架构**：
- `SharedTransitionLayout` 包裹 `NavHost`，提供跨路由的共享动画作用域
- `SharedTransitionScope` 通过 `CompositionLocal` 向下传递，避免 prop-drilling
- `AnimatedVisibilityScope` 从每个 `composable {}` lambda 传入子页面

**共享 key 格式**：`"media-thumbnail-{mediaId}-msg-{messageId}"`

> 关键细节：key 必须包含 `messageId`，否则当两个 MessageCard 包含同一个 Media 时，两个缩略图会同时注册相同 key，导致其中一个显示空白。

### 涉及文件

| 文件 | 改动 |
|------|------|
| `MainActivity.kt` | 添加 `LocalSharedTransitionScope`，用 `SharedTransitionLayout` 包裹 `NavHost`；`MESSAGE_LIST` 的 `popEnterTransition` 改为 `EnterTransition.None`（避免返回时出现滑入动画）；`MEDIA_FULLSCREEN` 路由添加 fade 过渡并传入 `animatedVisibilityScope` |
| `Navigation.kt` | `MEDIA_FULLSCREEN` 路由添加 `messageId` 参数；`navigateToMediaFullscreen()` 增加 `messageId` 参数 |
| `MessageListScreen.kt` | `onMediaClick` 签名增加 `messageId: Long` |
| `MessageCard.kt` | `MessageCard`、`MediaThumbnailGrid`、`MediaThumbnailItem` 均增加 `messageId` 参数；在 `MediaThumbnailItem` 中应用 `sharedElement` modifier |
| `MediaViewerScreen.kt` | 增加 `messageId` 参数；在 Pager 初始页应用 `sharedElement` modifier |

---

## 二、Telegram 风格视频播放器

### 问题

原 `VideoPlayer` 使用 `PlayerView(useController = true)`，ExoPlayer 默认控制器会在显示时对视频添加半透明遮罩（变灰），不符合 Telegram 风格。

### 实现：`TelegramVideoPlayer`（新增于 `VideoPlayer.kt`）

**核心**：`PlayerView` 设置 `useController = false`，所有控件由 Compose 自定义实现。

**行为**：

| 状态 | 显示内容 |
|------|---------|
| 默认 | 底部 2dp 白色 `LinearProgressIndicator`（永久，不可交互） |
| 点击后（3秒内）| 底部切换为可拖动 `Slider` + 左右时间标签；中央显示播放/暂停圆形按钮 |
| 3秒无操作 | 控件自动隐藏，恢复细进度条 |
| 拖动 Slider | 实时 seek，显示当前时间，松手后重置 3秒计时器 |

**播放/暂停图标**：
- 播放：`Icons.Default.PlayArrow`
- 暂停：`Canvas` 手绘两条矩形竖线（无需 `material-icons-extended` 依赖）

**关键参数**：
```kotlin
fun TelegramVideoPlayer(
    videoPath: String,
    autoPlay: Boolean = true,
    modifier: Modifier = Modifier
)
```

---

## 三、底部横向缩略图导航条

### 实现：`MediaStripBar`（`MediaViewerScreen.kt` 私有组件）

仅在 `mediaList.size > 1` 时显示。

**布局**：
- 固定在屏幕底部（`align(Alignment.BottomCenter)`），半透明黑色背景（alpha 0.55）
- `LazyRow`，60dp 正方形缩略图，`4dp` 间距，左右 `8dp` 内边距

**交互**：
- 点击缩略图 → `pagerState.animateScrollToPage(index)`
- Pager 滑动 → `LaunchedEffect(pagerState.currentPage)` 自动滚动 strip 到当前项

**视觉细节**：
- 选中项：2dp 白色边框，全亮度
- 未选中项：35% 黑色遮罩
- 视频缩略图：右下角小三角播放标记（`Canvas` 绘制）

**视频布局适配**：
- 有 strip 时，`TelegramVideoPlayer` 添加 `padding(bottom = 76.dp)`，避免自身进度条被遮挡
- 76dp = 60dp 缩略图 + 8dp×2 垂直内边距

---

## 关键决策记录

### 为什么 key 要包含 messageId？

`SharedTransitionLayout` 要求同一时刻屏幕上所有 `sharedElement` 的 key 全局唯一。若两条 Message 都包含同一个 Media，`"media-thumbnail-{mediaId}"` 会被注册两次，Compose 只保留一个 layout node，另一个渲染为空白。加入 `messageId` 后每个实例的 key 唯一，问题消除。

### 为什么 popEnterTransition 改为 None？

`MESSAGE_LIST` 原本设置了 `popEnterTransition = slideInFromLeft()`，从媒体查看器返回时会触发 Message 页面的滑入动画，与共享元素收缩动画冲突，视觉上产生两个动画叠加。改为 `EnterTransition.None` 后由共享元素动画独自主导过渡。
