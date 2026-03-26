# MediaManager 前端

基于 Vue 3 + TypeScript + Tailwind CSS 构建的个人媒体管理系统前端，采用类 Instagram 信息流架构。

## 技术栈

- Vue 3.5（Composition API + `<script setup>`）
- TypeScript
- Vite 7
- Vue Router 4（keep-alive 缓存）
- Tailwind CSS v4（Vite 集成）
- v-calendar 3（日历侧栏）
- PWA（Workbox）
- Capacitor 8（Android）

## 项目结构

```
src/
├── views/                  # 页面组件
│   ├── Message.vue         # 消息信息流（首页）
│   ├── Media.vue           # 媒体网格浏览
│   └── Actor.vue           # 演员列表
├── components/             # 可复用组件
│   ├── Navbar.vue          # 左侧导航栏
│   ├── BottomNavBar.vue    # 移动端底部导航
│   ├── MessageCard.vue     # 消息卡片
│   ├── MediaPreview.vue    # 全屏媒体预览
│   ├── CalendarSidebar.vue # 日历侧栏（v-calendar）
│   ├── ActorCard.vue       # 演员卡片
│   └── PwaInstallPrompt.vue
├── composables/            # 组合式函数
│   └── useTheme.ts         # 深色/浅色主题切换
├── utils/
│   └── constants.ts        # API_BASE_URL 等配置
├── router/
│   └── index.ts            # 路由配置（3 条路由）
├── App.vue                 # 根组件
└── main.ts                 # 应用入口
```

## 路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | Message | 消息信息流，支持搜索、#tag、附件上传、无限滚动、日历跳转 |
| `/media` | Media | 媒体网格，cursor 分页，类型筛选，全屏预览 |
| `/actor` | Actor | 演员列表（待迁移至新架构） |

## 核心功能

- **无限滚动** — 基于 IntersectionObserver + cursor 分页，支持双向加载（上/下）
- **日历侧栏** — 宽屏（≥1536px）右侧显示月历，标记有消息的日期，点击跳转/滚动到对应日期
- **全屏媒体预览** — 支持图片/视频，键盘导航
- **#标签系统** — 从消息文本自动解析
- **主题切换** — 深色/浅色模式，localStorage 持久化
- **keep-alive 缓存** — 页面切换保持滚动位置和状态
- **PWA** — 可安装为桌面/移动应用
- **Capacitor** — 原生 Android 支持

## 快速开始

```bash
pnpm install
pnpm dev
```

访问 http://localhost:5173

## 构建

```bash
pnpm build
```
