# 媒体信息管理系统

一个基于 Vue 3 + TypeScript + Tailwind CSS 构建的现代化媒体信息管理系统，支持人物、分组、媒体和标签的全方位管理。

## ✨ 功能特性

### 📱 核心模块

- **人物管理 (Person)**
  - 人物列表展示与搜索
  - 人物详情页面，展示关联的分组信息
  - 人物信息的添加、编辑、删除
  - 分组关联管理

- **分组管理 (Group)**
  - 分组列表展示与搜索
  - 分组详情页面，展示关联的媒体网格
  - 分组信息的添加、编辑、删除
  - 成员和媒体统计

- **媒体管理 (Media)**
  - 支持多种媒体类型：视频、图片、音频、文档
  - 媒体列表展示（网格布局）
  - 按类型和分组筛选
  - 媒体详情页面，支持在线预览
  - 上一个/下一个媒体导航（保持列表上下文）
  - 媒体信息的添加、编辑、删除
  - 标签关联管理

- **标签管理 (Tag)**
  - 标签列表展示与搜索
  - 按类型筛选标签
  - 标签信息的添加、编辑、删除
  - 显示每个标签关联的媒体数量
  - 媒体与标签的多对多关系管理

- **文章管理 (Article)**
  - Markdown 文章展示
  - 文章列表与搜索

### 🎨 用户体验

- **深色模式支持**
  - 全局深色/浅色主题切换
  - 主题偏好本地存储
  - 平滑的主题过渡动画

- **响应式设计**
  - 移动端、平板、桌面端完美适配
  - 灵活的网格布局系统

- **页面状态保持**
  - 使用 Vue Router 的 keep-alive 缓存页面
  - 页面切换时保持滚动位置
  - 保持筛选和搜索状态

- **优雅的交互**
  - 模态弹窗表单
  - 平滑的页面过渡效果
  - 加载状态提示
  - 操作确认对话框

## 🛠️ 技术栈

- **前端框架**: Vue 3 (Composition API + `<script setup>`)
- **开发语言**: TypeScript
- **构建工具**: Vite
- **路由管理**: Vue Router 4
- **样式方案**: Tailwind CSS 4
- **UI组件**: Headless UI (Dialog, Listbox, Transition)
- **Markdown渲染**: vue-markdown-render

## 📦 项目结构

```
src/
├── components/          # 可复用组件
│   ├── Navbar.vue      # 全局导航栏
│   ├── MediaCard.vue   # 媒体卡片
│   ├── PersonCard.vue  # 人物卡片
│   ├── GroupCard.vue   # 分组卡片
│   ├── TagCard.vue     # 标签卡片
│   ├── PersonEditModal.vue   # 人物编辑弹窗
│   ├── GroupEditModal.vue    # 分组编辑弹窗
│   └── TagEditModal.vue      # 标签编辑弹窗
├── views/               # 页面组件
│   ├── Home.vue        # 首页
│   ├── Person.vue      # 人物列表
│   ├── PersonDetail.vue # 人物详情
│   ├── Group.vue       # 分组列表
│   ├── GroupDetail.vue # 分组详情
│   ├── Media.vue       # 媒体列表
│   ├── MediaDetail.vue # 媒体详情
│   ├── Tag.vue         # 标签管理
│   └── Article.vue     # 文章列表
├── composables/         # 组合式函数
│   └── useTheme.ts     # 主题管理
├── data/                # 数据层
│   └── mockData.ts     # 模拟数据和辅助函数
├── router/              # 路由配置
│   └── index.ts
├── App.vue             # 根组件
└── main.ts             # 应用入口
```

## 🚀 快速开始

### 安装依赖

```bash
pnpm install
```

### 开发模式

```bash
pnpm dev
```

访问 http://localhost:5173 查看应用

### 构建生产版本

```bash
pnpm build
```

### 预览生产构建

```bash
pnpm preview
```

## 📊 数据模型

### 核心实体

- **Person**: 人物信息（姓名、简介、创建日期）
- **Group**: 分组信息（名称、描述、创建日期）
- **Media**: 媒体信息（名称、类型、描述、分组ID、创建日期）
- **Tag**: 标签信息（类型、名称）

### 关系表

- **PersonGroup**: 人物与分组的多对多关系
- **MediaTag**: 媒体与标签的多对多关系

## 🎯 核心功能说明

### 媒体详情页导航

在媒体详情页提供"上一个/下一个"按钮，根据进入页面时的列表上下文进行导航：
- 从媒体列表进入：按照过滤/搜索后的顺序导航
- 从分组详情进入：按照该分组的媒体顺序导航
- 使用 History State API 传递媒体列表，保持导航上下文

### 标签系统

- 标签与媒体建立多对多关系，通过 MediaTag 关联表管理
- 在媒体详情页可以添加/删除标签
- 支持标签搜索和类型筛选
- 显示每个标签关联的媒体数量

### Keep-alive 缓存

- 主要列表页面（Media, Person, Group, Tag, Article, Home）启用 keep-alive
- 页面切换时保持滚动位置和筛选状态
- 使用 onActivated/onDeactivated 生命周期钩子管理状态

## 🎨 主题系统

支持浅色和深色两种主题：
- 自动检测系统主题偏好
- 手动切换主题
- 主题偏好持久化存储
- 全局主题变量统一管理

## 📝 待办事项

- [ ] 接入真实后端 API
- [ ] 添加用户认证系统
- [ ] 实现文件上传功能
- [ ] 添加数据导入/导出
- [ ] 优化性能（虚拟滚动、懒加载）
- [ ] 添加单元测试

## 📄 许可证

MIT
