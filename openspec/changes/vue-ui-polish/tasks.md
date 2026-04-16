## 1. 基础设施：字体与色彩变量

- [x] 1.1 在 `vue/index.html` 中添加 Google Fonts 引用（Noto Serif SC + Noto Sans SC，font-display: swap）
- [x] 1.2 在 `vue/src/style.css` 中定义 `--font-display` / `--font-body` CSS 变量，设置 fallback 字体栈
- [x] 1.3 在 `vue/src/style.css` 中定义三层色彩变量：primary-500/600/700、success/warning/danger、扩展现有 surface 变量
- [x] 1.4 将 `App.vue` 和全局样式中的 `font-family` 替换为 CSS 变量引用

## 2. 全局动效基础

- [x] 2.1 在 `style.css` 中定义 `@keyframes fade-up`（opacity + translateY）和 `.animate-in` 触发类
- [x] 2.2 在 `style.css` 中定义 `@keyframes star-bounce`（scale 1→1.3→1）
- [x] 2.3 添加 `prefers-reduced-motion` 媒体查询，禁用所有自定义动画
- [x] 2.4 添加全局按钮 press 状态：`button:active, [role="button"]:active { transform: scale(0.96) }`

## 3. 确认弹窗组件

- [x] 3.1 创建 `vue/src/composables/useConfirm.ts`，暴露 `confirm()` promise API
- [x] 3.2 创建 `vue/src/components/ConfirmDialog.vue`，基于 HeadlessUI Dialog，支持 danger 模式
- [x] 3.3 在 `App.vue` 中挂载 `ConfirmDialog` 全局实例
- [x] 3.4 将 `Message.vue` 中的 `window.confirm()` 替换为 `useConfirm()`
- [x] 3.5 将 `Actor.vue` 中的 `window.confirm()` 替换为 `useConfirm()`
- [x] 3.6 将 `RecordDrawer.vue` 中的删除确认替换为 `useConfirm()`

## 4. 列表项进场动画

- [x] 4.1 在 `MessageCard.vue` 中添加 IntersectionObserver，进入视口时添加 `.animate-in` class
- [x] 4.2 实现 stagger 效果：通过 CSS 变量 `--stagger-index` 控制 animation-delay

## 5. 星标微动效

- [x] 5.1 在 `MessageCard.vue` 星标按钮点击时添加 `star-bounce` 动画 class
- [x] 5.2 在 `Media.vue` / `MediaFeed.vue` 网格星标按钮添加同样的 bounce 动画
- [x] 5.3 在 `MediaPreview.vue` 星标按钮添加同样的 bounce 动画

## 6. 面板与路由过渡

- [x] 6.1 为 `Message.vue` 右侧详情面板添加 `translateX` 滑入/滑出 CSS transition
- [x] 6.2 在 `App.vue` 的 `<router-view>` 外包裹 `<Transition>`，添加 fade + translateY 过渡

## 7. 视觉细节提升

- [x] 7.1 升级媒体网格 hover 效果：`MessageCard.vue` 媒体缩略图 hover 时 scale(1.05) + 暗色叠层
- [x] 7.2 升级 `Media.vue` / `MediaFeed.vue` 网格 hover 效果（同上）
- [x] 7.3 重设计 `Message.vue` 日期分隔符：毛玻璃胶囊 pill + sticky 定位
- [x] 7.4 为 `Message.vue` 空状态添加 CSS 几何插画
- [x] 7.5 为 `Media.vue` 空状态添加 CSS 几何插画

## 8. 色值迁移

- [x] 8.1 将 `Navbar.vue` 和 `BottomNavBar.vue` 中的硬编码 indigo/pink 替换为 CSS 变量
- [x] 8.2 将 `MessageCard.vue` 中的硬编码色值替换为 CSS 变量
- [x] 8.3 将 `SearchInput.vue`、`FilterSelect.vue` 中的硬编码色值替换为 CSS 变量
- [x] 8.4 将 `Message.vue`、`Actor.vue` 视图中的硬编码色值替换为 CSS 变量
