## 1. 后端 API

- [x] 1.1 新增 `backend/app/routers/admin.py`，实现 `GET /admin/stats` 端点，返回各表记录数和媒体存储统计
- [x] 1.2 在 `GET /admin/stats` 中查询最近 5 条 Message 作为 recent activity
- [x] 1.3 新增 `GET /admin/sync-logs` 端点，支持游标分页浏览 sync_log 表（该表无现有 API）
- [x] 1.4 在 `backend/app/__init__.py` 中注册 admin router

## 2. 前端路由与导航

- [x] 2.1 在 `vue/src/router/index.ts` 中新增 `/admin` 路由，使用懒加载 `() => import(...)`
- [x] 2.2 在 `vue/src/components/Navbar.vue` 中新增管理入口图标（使用齿轮/设置图标），带激活态样式
- [x] 2.3 在 `vue/src/components/BottomNavBar.vue` 中新增管理入口（若需要）

## 3. 管理页面框架

- [x] 3.1 创建 `vue/src/views/Admin.vue` 主视图，包含 Tab 切换结构（概览 / 表浏览）
- [x] 3.2 实现 Tab 切换逻辑，默认显示概览 Tab

## 4. 概览仪表盘

- [x] 4.1 创建 `vue/src/components/admin/AdminDashboard.vue` 组件
- [x] 4.2 调用 `/admin/stats` API 展示各表记录数卡片
- [x] 4.3 展示存储统计信息（总文件数、总大小，格式化 GB/MB）
- [x] 4.4 展示最近 5 条 Message 摘要列表
- [x] 4.5 实现刷新按钮重新获取统计数据

## 5. 表浏览器

- [x] 5.1 创建 `vue/src/components/admin/TableBrowser.vue` 组件，包含左侧表列表 + 右侧内容区布局
- [x] 5.2 实现表名列表（Message、Media、Actor、Tag、SyncLog），点击切换选中表
- [x] 5.3 创建 `vue/src/components/admin/DataTable.vue` 通用表格组件，接收数据和列定义
- [x] 5.4 定义各表的列配置（字段名、显示名、类型、是否可编辑），集中存放在配置对象中
- [x] 5.5 实现游标分页（上一页/下一页按钮），复用现有 API 端点
- [x] 5.6 实现搜索框，按文本字段筛选记录

## 6. 记录详情与编辑

- [x] 6.1 创建 `vue/src/components/admin/RecordDrawer.vue` 右侧抽屉面板组件
- [x] 6.2 点击表格行时在抽屉中展示记录所有字段
- [x] 6.3 实现可编辑字段的表单（根据配置中的 editable 标记）
- [x] 6.4 保存时调用对应实体的 PUT/PATCH API，成功后 toast + 刷新列表
- [x] 6.5 实现删除按钮，点击弹出确认对话框，确认后调用 DELETE API

## 7. 类型定义

- [x] 7.1 在 `vue/src/types.ts` 中新增 AdminStats 等接口定义
