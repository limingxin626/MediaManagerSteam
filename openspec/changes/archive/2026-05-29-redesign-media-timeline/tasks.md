## 1. 隐藏原生滚动条

- [x] 1.1 在 `vue/src/style.css` 中新增 `.scrollbar-hidden` 工具类（`scrollbar-width: none` + `::-webkit-scrollbar { display: none }`，保留滚动能力）
- [x] 1.2 在 `vue/src/views/Media.vue` 的 `scrollContainer` div（line 120）上追加 `scrollbar-hidden` 类
- [ ] 1.3 浏览器（Chrome / Firefox / Edge）验证：滚动条视觉消失，鼠标滚轮 / 触控板 / 键盘 PageDown 仍正常滚动 _(留给用户在 `pnpm dev` 后手测)_

## 2. DateScrubber 视觉重做

- [x] 2.1 重写 `vue/src/components/DateScrubber.vue` 模板：拆分为"左标签区 26px + 右刻度轨道 14px"两列，常驻宽度 `w-[28px] md:w-[40px]`
- [x] 2.2 渲染中央细线轴、月份小刻度（1.5px 高）、年份长刻度（3px 高），保持现有 `dateToPercent` 数学
- [x] 2.3 年份文字标签：垂直分布在左标签区，相邻 `top` 差 <8% 时折叠保留较新一年（仅折叠文字，刻度全部保留）
- [x] 2.4 当前位置指示器：6px 圆点 + 12px 横向引出短线 + 浮动"YYYY年M月"胶囊标签（`bg-black/70 dark:bg-white/15 backdrop-blur-md text-xs rounded-full px-2 py-0.5`）
- [x] 2.5 `timeline.length < 2` 时隐藏胶囊标签，仅渲染圆点
- [x] 2.6 胶囊在 `<640px` 屏宽下隐藏（`hidden sm:flex`）
- [x] 2.7 适配 `.dark` 主题色（中性石墨）— 使用现有 CSS 变量与 Tailwind `dark:` 前缀

## 3. 拖动气泡升级

- [x] 3.1 拖动 / 悬浮 tooltip 样式改为毛玻璃：`backdrop-blur-md bg-white/10 dark:bg-black/40 border border-white/15 shadow-lg text-xs`
- [x] 3.2 文字格式保持 "YYYY年M月D日"，位置算法（lines 156–161）不变
- [x] 3.3 验证 `@jump` / `@jump-final` 契约未变（Media.vue 的 `handleDateScrubberJump` / `JumpFinal` 仍工作）

## 4. 滚轮转发

- [x] 4.1 `DateScrubber.vue` 在根元素绑定 `@wheel.passive="onWheel"`，新增 `emit('wheel', deltaY: number)`
- [x] 4.2 `Media.vue` 在 `<DateScrubber>` 上接 `@wheel="(dy) => scrollContainer?.scrollBy({ top: dy })"`
- [ ] 4.3 验证：鼠标停在时间轴上滚动滚轮，媒体网格能同方向滚动相同距离；不触发 `preventDefault` _(留给用户手测)_

## 5. 动画与可访问性

- [x] 5.1 圆点 + 胶囊纵向位置使用 `transition-[top] duration-200 ease-out`
- [x] 5.2 全局 `@media (prefers-reduced-motion: reduce)` 下移除上述 transition
- [x] 5.3 拖动状态切换 `cursor: grabbing`

## 6. 端到端验证

- [ ] 6.1 启动 `pnpm dev`，浏览器打开 `/media`，验证：滚动条不可见、时间轴常驻、滚轮在时间轴上能滚列表 _(留给用户)_
- [ ] 6.2 拖动时间轴跳到任意年月，松手后媒体网格正确定位 _(留给用户)_
- [ ] 6.3 切换亮 / 暗主题，时间轴视觉协调，文字 / 刻度对比度足够 _(留给用户)_
- [ ] 6.4 触屏模拟（DevTools device toolbar）：触摸拖动仍工作；移动端宽度收窄至 28px、胶囊隐藏 _(留给用户)_
- [ ] 6.5 切到 Smart 搜索模式，时间轴消失，搜索结果可独立滚动 _(留给用户)_
- [x] 6.6 写当日开发日志到 `devlog/`（项目规则要求）
