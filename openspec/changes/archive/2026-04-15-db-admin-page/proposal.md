## Why

当前项目没有数据库管理界面，所有数据维护（修复坏数据、查看统计、批量操作）都需要直接操作 SQLite 文件。作为自托管的个人媒体管理系统，需要一个轻量的后台管理页面来查看和管理数据库中的记录，减少直接操作数据库的需求。

## What Changes

- 新增 `/admin` 前端路由，提供数据库管理界面
- 管理页面支持浏览所有数据库表（Message、Media、Actor、Tag、SyncLog）
- 每个表提供分页列表视图，支持搜索和筛选
- 支持查看单条记录详情、编辑字段、删除记录
- 提供数据库统计概览（各表记录数、存储占用等）
- 在侧边导航栏中新增管理入口

## Capabilities

### New Capabilities
- `db-admin-dashboard`: 数据库概览仪表盘，展示各表记录数和数据库统计信息
- `db-table-browser`: 通用表浏览器，支持逐表浏览、分页、搜索、排序、记录详情查看与编辑
- `db-admin-navigation`: 管理页面的导航集成（侧边栏入口、页面路由）

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **前端**：新增 Vue 视图组件和路由 (`/admin`)，Navbar 新增导航图标
- **后端**：可能需要新增通用查询 API 端点（或复用现有端点），新增统计 API
- **依赖**：无新增外部依赖
- **API**：新增 `GET /admin/stats` 统计端点；表数据复用现有 CRUD 端点
