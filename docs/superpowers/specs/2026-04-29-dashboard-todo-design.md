# 主页 Dashboard + Todo 看板 设计

日期：2026-04-29
状态：已确认

## 背景

当前主页（`vue/src/views/Home.vue`）只渲染一段静态 Markdown，其中包含一个手写 todo 列表，每完成一项需要手动编辑 Markdown 文本。目标是把主页改造成结构化 dashboard，使 todo 成为可交互的看板，并加入与项目数据相关的 widget。

## 目标

- 把主页变成多 widget 的固定网格 dashboard。
- Todo 看板支持 待办 / 进行中 / 已完成 三列、跨列拖拽、同列排序。
- 提供"最近媒体"和"统计卡"两个辅助 widget。
- 不保留旧的 Markdown 自由笔记区。

## 非目标

- 不做 todo 的截止日期、优先级、备注等额外字段（YAGNI，未来需要再加）。
- 不做 widget 的可拖拽自定义布局（固定网格即可）。
- 不做 todo 与 Message/Media 的关联跳转。
- 不做用户/权限相关功能（项目本身无 auth）。

## 数据模型

新增 `Todo` 表，独立模块 `backend/app/models/todo.py`：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int PK | 自增 |
| title | str (not null) | 标题文本 |
| status | str | `pending` / `doing` / `done` |
| position | int | 同列内顺序，越小越靠前 |
| created_at | datetime | 创建时间，默认 now |
| updated_at | datetime | onupdate=now |
| completed_at | datetime nullable | status 变 `done` 时填，反向清空 |

在 `backend/app/models/__init__.py` 中注册（参与 `Base.metadata.create_all`）。无外键，与现有 schema 完全独立。

## 后端 API

新增路由 `backend/app/routers/todos.py`，挂载到 `/todos`。

- `GET /todos`
  返回三列分组结构：
  ```json
  {
    "pending": [Todo, ...],
    "doing":   [Todo, ...],
    "done":    [Todo, ...]   // 仅最近 20 条，按 completed_at DESC
  }
  ```
  pending / doing 按 `position ASC` 排序，全量返回。

- `POST /todos` body `{ "title": str, "status"?: str }`
  默认 `status=pending`，新条目 `position` = 该列当前 max(position)+1。

- `PATCH /todos/{id}` body `{ "title"?: str }`
  仅允许改 title。

- `PATCH /todos/{id}/move` body `{ "status": str, "position": int }`
  跨列或同列移动。service 重排：
  1. 取目标列所有 todo（按 position 排序），移除当前 todo（如来自同列）。
  2. 在新 position 处插入。
  3. 整列重新写 0..N-1 的连续 position。
  4. 如果是跨列移动，源列同样压缩 position。
  5. status 变成 `done` 时设置 `completed_at=now()`；从 `done` 移走时设回 `None`。

- `DELETE /todos/{id}`
  物理删除。

Service 层 `backend/app/services/todo_service.py` 封装 move 的 position 重排逻辑，路由层只做参数校验和 commit。

### 统计端点

新增 `GET /stats`（路由 `backend/app/routers/stats.py`），返回：
```json
{
  "message_count": int,
  "media_count": int,
  "media_this_month": int,
  "todo_doing_count": int
}
```
单次聚合查询完成；`media_this_month` 按 `created_at >= 当月 1 日 00:00` 统计。

## 前端

### 依赖

新增 `vuedraggable@^4`（Vue 3 兼容版，底层是 SortableJS）。

### 类型

`vue/src/types.ts` 新增：
```ts
export type TodoStatus = 'pending' | 'doing' | 'done'
export interface Todo {
  id: number
  title: string
  status: TodoStatus
  position: number
  created_at: string
  updated_at: string
  completed_at: string | null
}
export interface TodoBoard {
  pending: Todo[]
  doing:   Todo[]
  done:    Todo[]
}
export interface DashboardStats {
  message_count: number
  media_count: number
  media_this_month: number
  todo_doing_count: number
}
```

### 组件结构

```
views/Home.vue                               <- dashboard 容器
└── components/dashboard/
    ├── TodoBoard.vue                        <- 三列看板（占整宽）
    │   └── TodoColumn.vue                   <- 单列：标题 + draggable list + 新增框（仅 pending 列显示新增框）
    │       └── TodoCard.vue                 <- 单卡：title + 编辑/删除
    ├── RecentMedia.vue                      <- 调 GET /media?limit=12，9~12 宫格缩略图，点击跳 /media
    └── StatsCard.vue                        <- 调 GET /stats，4 个数字卡平铺
```

### 布局

`Home.vue` 纵向叠加：
1. `TodoBoard`（占整宽，三列等分；移动端自动堆叠为单列）
2. 一行两栏：左 `RecentMedia` 占 2/3，右 `StatsCard` 占 1/3（移动端堆叠）

使用 Tailwind grid：`grid grid-cols-1 lg:grid-cols-3 gap-4`，`RecentMedia` 用 `lg:col-span-2`。

### 拖拽行为

`TodoBoard.vue` 维护本地三个数组，传给 `vuedraggable` 的 `v-model`，三列共享同一 `group="todos"` 以支持跨列。

`@end` 事件触发后：
1. 从事件中得到 `to.dataset.status`（目标列）和新 index。
2. 立即更新本地数组（乐观更新）。
3. 调 `PATCH /todos/{id}/move`。
4. 失败：调用 `useToast` 报错，重新 `GET /todos` 拉一次覆盖本地。

### 新增 / 编辑 / 删除

- 新增：pending 列底部一个输入框，回车提交 → `POST /todos` → 把返回值 push 到 pending。
- 编辑标题：双击卡片切换为 `<input>`，blur 或回车 → `PATCH /todos/{id}`。
- 删除：卡片 hover 时显示 ✕ 按钮 → 确认对话框（用 `confirm()` 或 HeadlessUI Dialog）→ `DELETE /todos/{id}`。

### 已有 Markdown 主页

完全替换为新 dashboard。旧的 Markdown 渲染逻辑及依赖如未在他处使用则一并移除，避免死代码。

## 错误处理

- 后端 move 接口校验：`status` 必须三选一、`position >= 0`，否则 422。`id` 不存在 404。
- 前端所有失败均通过 `useToast` 提示，并对受影响 widget 重新拉取（不在异常状态下卡住界面）。

## 测试

- 后端：用 pytest（如项目已有测试基建）覆盖：
  - 创建 todo，position 递增。
  - move 跨列后两列 position 都连续 0..N-1。
  - move 到 done 写 completed_at；移出 done 清空。
  - GET /todos 的 done 列只返回 20 条。
- 前端：手测拖拽（同列重排、跨列、跨列到指定位置、刷新后保持）；新增/编辑/删除冒烟。

## 开发日志

实现完成后按项目惯例追加一篇当日开发日志。

## Open Questions

无（设计已锁定）。
