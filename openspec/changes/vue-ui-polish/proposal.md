## Why

当前 Vue 前端功能完整，但视觉和交互停留在 "Tailwind 原型" 阶段——缺乏字体个性、动效反馈和操作层次感。用户日常高频使用的 feed 浏览、收藏、删除等操作都没有视觉反馈，页面切换是硬切，整体感知质量与功能成熟度不匹配。通过一轮系统性的 UI 打磨，可以将体验从 "能用" 提升到 "好用"。

## What Changes

### P0（高影响、低成本）
- 引入品牌字体（Noto Serif SC + Noto Sans SC），通过 CSS 变量统一管理
- MessageCard 列表项进场动画（IntersectionObserver 触发 fade-up stagger）
- 星标 toggle 微动效（scale bounce + CSS keyframes）
- 用 HeadlessUI Dialog 替换所有 `window.confirm()` 调用，统一确认弹窗风格
- Message 详情面板加入 `translateX` 滑入过渡动画

### P1（中等投入、显著提升）
- 媒体网格 hover 效果（scale + 暗色叠层 + 操作按钮浮现）
- 日期分隔符重设计（毛玻璃胶囊 pill + 装饰线条 + sticky 定位）
- 空状态用 CSS 几何插画替代纯文字
- 路由切换加 `<Transition>` fade/slide 过渡
- 所有按钮增加 `active:scale-[0.96]` press 状态反馈
- 色彩系统升级：建立 primary / semantic / surface 三层 CSS 变量体系

## Capabilities

### New Capabilities
- `ui-motion-system`: 全局动效体系——列表进场动画、星标微动效、面板过渡、路由切换过渡、按钮 press 状态
- `ui-visual-system`: 视觉体系升级——品牌字体引入、色彩变量重构、媒体网格 hover、日期分隔符重设计、空状态插画
- `confirm-dialog`: 统一确认弹窗组件，替换 window.confirm()

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **前端代码**: `vue/src/style.css`（字体、色彩变量、全局动效类）、所有 `.vue` 组件（按钮 active 状态、confirm 替换、动效 class）
- **依赖**: 新增 Google Fonts 引用（Noto Serif SC / Noto Sans SC）
- **后端**: 无影响
- **兼容性**: 纯 CSS 动效，无浏览器兼容风险；字体通过 CDN 加载，离线时 fallback 到系统字体
