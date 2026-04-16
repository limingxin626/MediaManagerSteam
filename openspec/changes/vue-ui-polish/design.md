## Context

当前 Vue 前端使用 Tailwind v4 + HeadlessUI，暗色主题有温暖的紫色渐变底色。功能完整（消息 feed、媒体网格、演员管理、灯箱预览），但视觉层面完全依赖 Tailwind 默认值——系统字体、indigo-600 一把梭、无进场/过渡动效、`window.confirm()` 原生弹窗。需要一轮系统性打磨来提升感知质量。

技术栈约束：Vue 3.5 `<script setup>` + TypeScript + Tailwind v4（Vite 插件）+ HeadlessUI。不引入额外 JS 动画库，优先纯 CSS 方案。

## Goals / Non-Goals

**Goals:**
- 建立统一的品牌字体 + 色彩变量体系，替换散落在组件中的硬编码值
- 为高频交互（列表浏览、收藏、删除确认、面板切换）加入动效反馈
- 提升媒体网格、日期分隔符、空状态的视觉表现力
- 所有改动向后兼容，不改变功能逻辑

**Non-Goals:**
- 不做主题色板切换（森林/海洋等）——留给后续迭代
- 不做拖拽排序、手势操作——属于交互功能，不是视觉打磨
- 不做滚动视差——性能开销大，收益不确定
- 不引入 Motion / GSAP 等 JS 动画库

## Decisions

### 1. 字体方案：Google Fonts CDN 引入 Noto 系列
- **选择**: Noto Serif SC（标题/强调）+ Noto Sans SC（正文/UI）
- **替代方案**: 思源宋体本地打包——增加 bundle 体积 ~5MB，不值得
- **理由**: Noto 系列对中文支持最全，Google Fonts 按需加载子集，首屏影响小。离线时 fallback 到系统字体

### 2. 动效方案：纯 CSS + IntersectionObserver
- **选择**: CSS `@keyframes` + `animation-delay` 做 stagger，IntersectionObserver 触发 `.animate-in` class
- **替代方案**: Vue `<TransitionGroup>` 内置——对 infinite scroll 场景不友好，新增元素和初始渲染难以区分
- **理由**: CSS 动画性能好（GPU 加速），不依赖 JS 帧循环，代码量小

### 3. 确认弹窗：新建 `ConfirmDialog.vue` 组件
- **选择**: 基于 HeadlessUI `Dialog`，通过 composable `useConfirm()` 暴露 promise 式 API
- **替代方案**: 每个调用处内联 Dialog——重复代码多
- **理由**: `const ok = await confirm({ title, message, danger: true })` 比 `window.confirm()` 只多一行 import，迁移成本极低

### 4. 色彩变量重构：三层体系
- **选择**: `--color-primary-*`（品牌）、`--color-success/warning/danger`（语义）、`--bg-*` + `--text-*`（表面），全部定义在 `style.css` `:root` 中
- **理由**: 当前 indigo-600 既做 CTA 又做 active 又做 focus ring，语义不清。分层后可独立调整

### 5. 路由过渡：fade + translateY
- **选择**: `<router-view v-slot>` + `<Transition>` 包裹，CSS `opacity + translateY(8px)` 过渡 200ms
- **理由**: 轻量、不影响 `<keep-alive>` 缓存逻辑，与 Message view 的 `v-show` 策略兼容

## Risks / Trade-offs

- **Google Fonts CDN 依赖** → LAN 部署时可能加载慢或失败。Mitigation: CSS `font-display: swap` + 系统字体 fallback，字体加载失败不影响功能
- **动效过多可能影响低端设备** → Mitigation: 使用 `prefers-reduced-motion` 媒体查询全局禁用动画
- **色彩变量重构涉及多文件改动** → Mitigation: 先在 `style.css` 定义变量，再逐组件替换，可分步合入
