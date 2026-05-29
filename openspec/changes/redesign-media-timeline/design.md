## Context

Media 页面使用 `useVirtualGrid` 实现虚拟化网格，外层 `<div ref="scrollContainer" class="absolute inset-0 overflow-y-auto">` 提供滚动。当前 `DateScrubber.vue` 以 `absolute right-0 top-0 bottom-0 z-30` 浮在右侧，覆盖了原生滚动条所在的 8px 区域，造成"滚动条点不到"。

`DateScrubber` 现有的核心逻辑健壮可复用：
- `dateToPercent / percentToDate / yToPercent`（lines 86–101）
- 拖动节流（`requestAnimationFrame`，lines 175–183）
- `@jump`（拖动中预览）与 `@jump-final`（释放后落定）的双事件契约（Media.vue line 174-175 已对接 `useVirtualGrid.scrollToDate`）

主题系统：`useTheme` 切换 `.dark` 类，配色走 CSS 变量（`--color-primary-500` 等）。

## Goals / Non-Goals

**Goals:**
- 滚动条彻底从 Media 页面视觉上消失，时间轴成为唯一纵向定位控件。
- 时间轴在不悬浮时也能一眼看清年份与当前所在月份。
- Apple Photos 风格的指示器（圆点 + 引出线 + 浮动月份胶囊标签）。
- 鼠标滚轮在时间轴区域上仍能滚动媒体列表。
- 保持现有 `@jump / @jump-final` 契约与 `useVirtualGrid` 解耦，无需改动虚拟网格代码。

**Non-Goals:**
- 不改 `useVirtualGrid` 的内部数据结构或加载策略。
- 不引入新的依赖（不引入 d3、framer-motion 等）。
- 不为 Smart 模式（搜索结果）添加时间轴 —— 维持现有 `v-if="!smartActive"` 守卫。
- 不做横屏移动端的特别优化（手机仍以现有触摸拖动为主）。

## Decisions

### 1. 隐藏原生滚动条而非用第三方虚拟滚动条
- **选**：在 `style.css` 新增 `.scrollbar-hidden` 工具类，使用 `scrollbar-width: none` (Firefox) 和 `::-webkit-scrollbar { display: none }` (Chromium/Safari)，仍保留 `overflow-y: auto` 滚动能力。施加在 Media.vue 的 `scrollContainer` 上。
- **拒**：引入 OverlayScrollbars 等库 —— 额外依赖，且本就要"消除"滚动条视觉。

### 2. 时间轴常驻 40px，分为"刻度轨道（右）+ 标签区（左）"两列
- 右侧 14px：中央细线 + 月份小刻度（1.5px）+ 年份长刻度（3px）+ 圆点指示器。
- 左侧 26px：年份文字（垂直分布、靠近年份刻度），与当前月份胶囊标签水平对齐位置。
- 当前位置指示器：6px 圆点 + 向左的 12px 短引出线，连接到一个 `bg-black/70 backdrop-blur-md text-white text-xs rounded-full px-2 py-0.5` 的"YYYY年M月"胶囊，水平位于时间轴左侧 ~30px 处。

### 3. 拖动气泡升级为毛玻璃
- 沿用现有 tooltip 位置算法（lines 156–161），但样式换为 `backdrop-blur-md bg-white/10 dark:bg-black/40 border border-white/15 shadow-lg`，显示完整 `YYYY年M月D日`。

### 4. 滚轮转发（关键交互修复）
- 在 `DateScrubber` 根元素上绑定 `@wheel="onWheel"`，handler 通过 `props` 暴露的 `scrollTarget?: HTMLElement` 或新增 `emit('wheel', deltaY)`。
- **选**：用 emit (`@wheel="(dy) => scrollContainer.scrollBy({ top: dy })"`)，让 Media.vue 持有滚动容器引用，组件本身保持无副作用。
- 不调用 `e.preventDefault()`，仅当滚轮事件实际被拦截在时间轴上时转发，避免影响嵌套滚动场景。

### 5. 年份标签防重叠
- 现有逻辑 (lines 136–151) 已处理首尾边界，但当总跨度较小（<2 年）时多个标签可能挤一起。新增最小间距过滤：相邻两个年份标签 `top` 差 <8% 时只保留较新的那个；保留所有年份的刻度，仅折叠文字。

### 6. 动画与可访问性
- 指示器 `transition-[top] duration-200 ease-out`；胶囊标签整体 `transition-opacity`。
- `@media (prefers-reduced-motion: reduce)` 下移除 transition。
- 拖动状态加 `cursor: grabbing` + 整体 background 渐变保持现有逻辑。

### 7. 移动端宽度
- `w-[28px] md:w-[40px]`，胶囊标签在 <640px 屏幕隐藏（仅保留圆点 + 引出线），避免占用过多宽度。

## Risks / Trade-offs

- **[风险]** 隐藏滚动条后，键盘 Page Up/Down 与触控板"按住右边滑"的手势仍然可用，但用户可能不熟悉无滚动条的交互 → **缓解**：保留"回到最新"按钮 + 时间轴本身高频可见，作为定位补偿。
- **[风险]** Apple Photos 风格指示器多了引出线和胶囊，在数据稀疏（只有 1–2 个月）时显得空 → **缓解**：仅当 `timeline.length >= 2` 时显示胶囊标签，否则只显示圆点（与现有 `v-if` 守卫一致）。
- **[风险]** 滚轮转发 emit 在频繁滚动时可能产生大量事件 → **缓解**：不做节流（浏览器原生 wheel 频率已可控），`scrollBy` 同步操作开销极小。
- **[Trade-off]** 不再支持"窄态隐藏，宽态展开"的渐进式呈现，换来"常驻可见、信息密度更高"的体验，与 Photos/Google Photos 风格一致。

## Migration Plan

无数据迁移。代码层面：

1. 改 `style.css`、`Media.vue` 滚动容器隐藏 scrollbar。
2. 重写 `DateScrubber.vue` 模板与样式，保留 props/emit 契约。
3. 在 Media.vue 上接 `@wheel` 转发到 `scrollContainer`。
4. 浏览器手测（亮/暗 + 桌面/移动模拟器）。

回滚：单一组件 + 单一 CSS 类，`git revert` 即可。

## Open Questions

无（已通过 AskUserQuestion 与用户确认视觉风格、宽度、滚轮转发策略）。
