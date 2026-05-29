## Context

`MediaPreview.vue` 是 Message Feed 等场景下使用的全屏弹层。底部 thumbnail strip 通过 `overflow-x-auto` + `justify-center` 容器实现，每次切换 `currentIndex` 后调用 `scrollIntoView({ inline: 'center', block: 'nearest' })`。

两个问题的根因：

1. **居中失效**：容器同时使用 `justify-center` 与 `overflow-x-auto`。当 thumbnails 总宽小于容器宽时，flex 居中生效但内容不会溢出，`scrollIntoView` 没有滚动空间；当总宽大于容器时，flex 会把内容左对齐压缩起点，浏览器 `scrollIntoView({inline: 'center'})` 又会把元素恰好滚到视口中点。但因为 `justify-center` 在内容超出时会产生不可滚动的左侧负空白，导致左侧若干项无法滚到中心，给人"不居中"的错觉。
2. **无过渡**：模板里 `<video>` / `<img>` 直接通过 `currentItem`/`getMediaUrl` 切换源，DOM 节点复用、src 替换瞬间发生，没有 `<Transition>` 包裹。

UI motion 约定见 `openspec/specs/ui-motion-system/spec.md`（短促、缓动平滑、移动端友好）。

## Goals / Non-Goals

**Goals:**
- Thumbnail strip 在任何 `items.length` 下都把当前缩略图水平居中。
- 主图切换具备方向感（左/右）的进入/退出动画，过渡时长 ~200ms。
- 键盘连续翻页（按住箭头）不能因为动画产生明显卡顿或视觉堆叠。

**Non-Goals:**
- 不调整 toolbar、tag、删除/旋转/替换等已有功能。
- 不引入手势滑动切换（swipe）——现有左右按钮 + 键盘已够用，留待后续。
- 不改 MediaDetail 全屏页。

## Decisions

### D1：去掉 `justify-center`，改用 padding + 程序化居中

放弃 flex `justify-center`，容器使用 `overflow-x-auto` 加左右内边距（例如 `px-[50%]` 或 JS 动态 padding），让任意一项都能滚到几何中点。或更简单：保留 `justify-center`，但在内容总宽超过容器宽时切换到 `justify-start`；切换后用 `scrollLeft = thumb.offsetLeft + thumb.offsetWidth/2 - container.clientWidth/2` 显式居中。

**选定方案**：用 ResizeObserver/计算容器内容宽度，**当总宽 ≤ 容器宽时使用 `justify-center` 且不滚动；总宽 > 容器宽时切换到 `justify-start` 并用 `scrollLeft` 手算居中**，避免 `scrollIntoView` 的边界行为。

**Alternative considered**：`px-[50%]` sentinel padding（Apple Photos 风格）——会让首末项可以滚到正中。简单但视觉上会留下大块空白，与现有紧凑风格不符。

### D2：主图切换用 Vue `<Transition mode="out-in">` + 方向感 class

用一个 `<Transition>` 包裹媒体容器，key 绑定 `currentItem?.id`，根据切换方向（prev/next）动态设置 `name="slide-left" | "slide-right"`，定义 `transform: translateX(±20px) + opacity` 过渡 200ms ease。

`mode="out-in"` 保证同一时间只有一个媒体元素存在，避免两个 `<video>` 同时播放抢音轨。代价是退出 + 进入串行，总耗时 ~400ms——对人眼仍可接受，且不会影响 `currentIndex` 立即更新（缩略图条会先于动画完成居中）。

**Alternative considered**：`mode="default"` 并存让两张图交叉淡入——视觉更顺滑，但 video 需要额外暂停旧元素的逻辑且会闪一下。优先保稳。

### D3：方向追踪

新增 `transitionName` ref。`prev()` 设 `slide-right`，`next()` 设 `slide-left`，缩略图点击根据新旧 index 比较确定方向。`watch(currentIndex)` 仍负责播放和滚动居中，但方向必须在 index 改变**前**设好——因此把方向设置逻辑放进 `prev()` / `next()` / thumb click handler 内同步执行。

## Risks / Trade-offs

- **键盘连按可能产生视觉堆积**：`out-in` 串行需 ~400ms 完成；用户连按方向键时新 index 立即生效但动画还在播旧的退出。Mitigation：动画时长压到 180ms，使用 `ease-out`；不阻塞 index 切换。
- **视频切换音频中断**：`out-in` 让旧 `<video>` 卸载，自然停播——好处而非风险。
- **手动计算 `scrollLeft` 与 ResizeObserver 的兼容性**：所有目标浏览器（Chrome/Edge/Electron/Android WebView）均支持，无需 polyfill。
- **旋转中切换**：现有 `watch(currentIndex)` 会把 `rotationDegrees` 归零，过渡期间用户视觉上看到从旋转态弹回——可接受，不需额外处理。
