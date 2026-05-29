## Why

Media 页面右侧的 `DateScrubber` 时间轴与浏览器原生滚动条同时渲染，两者在 `right: 0` 位置完全重叠。`DateScrubber` 以 `z-30` 盖在滚动条上方，导致用户点不到滚动条；同时时间轴本身的视觉表达较弱（仅细线 + 月/年刻度），既不够直观也不够美观。需要让时间轴成为唯一的纵向导航控件，并提升其视觉与交互质感。

## What Changes

- **BREAKING**：移除 Media 页面滚动容器的原生滚动条显示（保留滚动能力，隐藏 scrollbar）。
- 重做 `DateScrubber` 组件为 Apple Photos 风格的常驻时间轴：
  - 常驻宽度约 40px，无需 hover 即可看清年份标签和月份刻度。
  - 中央细轴 + 年份分段（明显分隔线 + 年份文字），月份小刻度。
  - 当前位置指示器升级为带渐变光晕的圆点 + 横向引出短线，连到一个浮动的"年-月"胶囊标签。
  - 拖动时显示带毛玻璃 (`backdrop-blur`) 的日期气泡。
- 让滚轮在时间轴上滚动时，事件被转发到主滚动容器（用户把鼠标停在右边缘也能正常滚动列表）。
- 适配亮色 / 暗色（中性石墨）主题；尊重 `prefers-reduced-motion`。
- 移动端（触屏）保持现有拖动交互，但默认收窄至 ~28px，避免占太多视口宽度。

## Capabilities

### New Capabilities
- `media-timeline`: Media 页面右侧的纵向时间轴导航控件，作为唯一的滚动定位手段（替代原生滚动条），提供年份/月份可视化、当前位置指示、拖动跳转、滚轮转发等行为。

### Modified Capabilities
<!-- 无 -->

## Impact

- 受影响代码：
  - `vue/src/components/DateScrubber.vue`（重做模板、样式、新增滚轮转发）
  - `vue/src/views/Media.vue`（滚动容器加 `scrollbar-hidden` 类、调整时间轴占位）
  - `vue/src/style.css`（新增隐藏 scrollbar 的工具类，保留 `overflow` 滚动能力）
- 不影响 API、数据库、Android 端。
- 不影响 `useVirtualGrid` 的滚动 / 加载逻辑：`scrollToDate`、`currentDate` 等公共契约保持不变。
