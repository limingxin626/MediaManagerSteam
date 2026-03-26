# MediaManagerSteam — 项目现状 (2026-03-26)

## 项目简介

个人相册/媒体管理 App，已从**分类管理系统**转型为类似 **Instagram 信息流**的架构。
前端 Vue 3 PWA + 后端 FastAPI，面向局域网自托管使用。

---

## 整体架构

```
MediaManagerSteam/
├── backend/        FastAPI, Python, SQLAlchemy, SQLite
│   └── api.py      入口, uvicorn 0.0.0.0:8002
├── vue/            Vue 3 + Tailwind CSS v4 + TypeScript, PWA + Capacitor
│   └── src/
└── electron/       Electron 桌面端封装
```

**API Base URL:** `http://192.168.31.146:8002`

---

## 后端现状

### 已完成（新架构）

| 模块 | 路由前缀 | 状态 |
| ---- | -------- | ---- |
| 消息流 | `/messages` | ✅ 完整 CRUD，cursor 分页，#tag 解析 |
| 媒体文件 | `/media` | ✅ cursor 分页，rating/view count |
| 文件操作 | `/files` | ✅ list/move/rename/upload/upload-media |
| 演员 | `/actors` | ✅ 列表+详情（含消息列表） |
| 标签 | `/tags` | ✅ 搜索+消息数统计 |

### 已删除（旧架构残留）

- `services/actor.py`, `services/media.py`, `services/tag.py`
- `services/article.py`, `services/group.py`, `services/legacy.py`, `services/stats.py`, `services/media_tag.py`
- `models/model_old.py`

### Services（新）

- `media_service.py` — 文件哈希去重、媒体信息提取、缩略图生成
- `message_service.py` — #hashtag 解析、媒体排序

---

## 前端现状

### 路由与页面

| 路由 | 组件 | 状态 | 说明 |
| ---- | ---- | ---- | ---- |
| `/` | Message.vue | ✅ | 信息流首页，无限滚动，#tag，附件上传，toast 通知 |
| `/media` | Media.vue | ✅ | 媒体网格，useInfiniteScroll cursor 分页，类型筛选，全屏预览 |
| `/actor` | Actor.vue | ✅ | 演员管理，无限滚动，排序/筛选，CRUD UI（后端待补 POST/PUT/DELETE） |
| `/:pathMatch(.*)*` | NotFound.vue | ✅ | 404 页面 |

### 基础设施

| 模块 | 文件 | 说明 |
| ---- | ---- | ---- |
| API 服务层 | `composables/useApi.ts` | `api.get/post/put/patch/del`，204 处理，`ApiError`，`useInfiniteScroll` composable |
| Toast 通知 | `composables/useToast.ts` | 单例 reactive，success/error/info，自动消失 |
| 媒体工具 | `utils/media.ts` | `formatDuration`, `isVideo`, `isImage`, `getThumbUrl`, `getActorCoverUrl` |

### 组件

| 组件 | 状态 | 说明 |
| ---- | ---- | ---- |
| MessageCard.vue | ✅ | 消息卡片，媒体网格，tag 展示，菜单操作 |
| MediaPreview.vue | ✅ | 全屏媒体预览，键盘导航 |
| ActorCard.vue | ✅ | 演员卡片，封面图，分类/评分/下载状态 |
| ActorEditModal.vue | ✅ | 演员新增/编辑弹窗 |
| FilterSelect.vue | ✅ | 通用筛选下拉 |
| ToastContainer.vue | ✅ | 右上角 toast 堆叠，Teleport + TransitionGroup |
| Navbar.vue | ✅ | 左侧 sidebar，桌面端显示（`hidden md:flex`） |
| BottomNavBar.vue | ✅ | 移动端底栏（`md:hidden`） |
| PwaInstallPrompt.vue | ✅ | PWA 安装提示 |

### 已清理的废弃文件

Home.vue, HelloWorld.vue, ViewToggle.vue, PreviewCard.vue, MediaCard.vue, MediaEditModal.vue, MediaTagModal.vue, PaginationBar.vue — 均已删除

### 技术栈

- Vue 3.5 + `<script setup>` + TypeScript
- Tailwind CSS v4（Vite 集成）
- Vue Router 4（lazy loading，keep-alive 缓存 Media/Actor/Message）
- Vite 7 + PWA（Workbox）
- Capacitor 8（Android）
- **无 Pinia/Vuex**，全局状态通过 composable + localStorage

---

## 已完成

- ✅ 消息流核心功能（Message.vue）— 无限滚动，搜索，#tag，toast 错误/成功提示
- ✅ 媒体网格浏览（Media.vue）— useInfiniteScroll cursor 分页，类型筛选，全屏预览
- ✅ 演员管理（Actor.vue）— 迁移至 `/actors` API，无限滚动，CRUD UI
- ✅ API 服务层（useApi.ts）— 统一 fetch 封装，IntersectionObserver 无限滚动 composable
- ✅ Toast 通知系统 — useToast + ToastContainer
- ✅ 工具函数抽取（utils/media.ts）— 消除跨组件重复定义
- ✅ 移动端响应式布局 — sidebar 隐藏，底部导航，fixed 元素适配
- ✅ 路由增强 — lazy loading + 404 catch-all
- ✅ 废弃文件清理 — 删除 8 个无用组件/页面
- ✅ 类型统一 — CursorResponse<T> 泛型，移除 inline 类型定义
- ✅ Bug 修复 — Message.vue sendMessage 响应处理、deleteMessage 204 处理
- ✅ 路由精简为 4 条（`/`, `/media`, `/actor`, `404`）
- ✅ 导航栏更新（Navbar + BottomNavBar）
- ✅ 后端新架构全部 API

## 待完成

- [ ] 后端补充 Actor CRUD API（POST/PUT/DELETE /actors）
- [ ] Media.vue 类型筛选对接后端（当前后端 cursor API 未支持 type 参数）
- [ ] MessageCard.vue 移除未使用的 `click` emit
- [ ] 迁移数据库以支持收藏

---

## 数据库

SQLite，路径通过 `ASKTAO_DATA_ROOT` 环境变量配置。
