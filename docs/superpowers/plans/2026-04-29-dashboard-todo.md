# 主页 Dashboard + Todo 看板 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把现有 Markdown 主页改造成结构化 dashboard，包含可拖拽的 Todo 看板（待办 / 进行中 / 已完成）、最近媒体九宫格、统计卡四件，使日常 todo 管理无需再编辑 Markdown 文本。

**Architecture:** 后端新增独立 `Todo` 表 + `/todos` REST 路由 + `/api/dashboard/stats` 聚合端点（复用现有 dashboard router 前缀）。前端 `views/Dashboard.vue` 重写为 widget 容器，子组件 `TodoBoard / RecentMedia / StatsCard` 各司其职。Todo 移动通过 `vuedraggable` 跨列拖拽，单个 `PATCH /todos/{id}/move` 提交目标列+目标位置，后端原子重排该列 position。

**Tech Stack:** FastAPI + SQLAlchemy + SQLite + Alembic（后端）；Vue 3 `<script setup>` + TypeScript + Tailwind v4 + vuedraggable@4（前端）。

**项目背景注意事项：**
- 旧主页（基于 markdown 文件 + `/api/dashboard` GET/PUT）将被新 dashboard 完全替换。`backend/app/routers/dashboard.py` 中的 markdown 读写端点和默认模板逻辑、`backend/app/config.py` 中 `DASHBOARD_DEFAULT_CONTENT` 与 `get_dashboard_md_path()`、`vue/src/views/Dashboard.vue` 现有内容均要清理。
- 项目无后端测试基建（pyproject 没 pytest，没 backend/tests/），spec 中提到的 pytest 改为：手测命令 + 浏览器手测，明确写在每个验证步骤里。
- 路由前缀不一致：现有路由除 `dashboard` 用 `/api/dashboard` 外，其余直接 `/messages` `/media` 等。新 todos 路由用 `/todos`（跟随多数）；stats 复用 `/api/dashboard/stats`（跟随同 widget 主页相关语义）。
- 数据库通过 alembic 迁移；不要直接靠 `Base.metadata.create_all`。

**前置准备（人工，无需写在任务内）：** 计划假定开发者已经 `cd backend && uv pip install -e .` 与 `cd vue && pnpm install` 过一次。每个改动 vue 依赖的任务会单独提示运行 `pnpm install`。

---

## 文件结构

**后端创建：**
- `backend/app/models/todo.py` — `Todo` ORM 模型（独立模块，从 `models/__init__.py` 导入）
- `backend/app/schemas/todo.py` — Pydantic schema：`TodoBase / TodoCreate / TodoUpdate / TodoMove / TodoOut / TodoBoard`
- `backend/app/services/todo_service.py` — 列内/跨列重排核心逻辑
- `backend/app/routers/todos.py` — `/todos` 路由 5 个端点
- `backend/alembic/versions/20260429_<rev>_add_todo.py` — 新表迁移

**后端修改：**
- `backend/app/models/__init__.py` — 导入 `Todo` 让 `Base.metadata` 能看见（供 alembic autogenerate）
- `backend/app/routers/__init__.py` — 注册 `todos_router`
- `backend/app/routers/dashboard.py` — 删除 markdown 读写端点；新增 `GET /api/dashboard/stats`
- `backend/app/config.py` — 移除 `DASHBOARD_DEFAULT_CONTENT` 和 `get_dashboard_md_path()`（如未在他处使用）

**前端创建：**
- `vue/src/components/dashboard/TodoBoard.vue` — 三列容器，处理拖拽事件，向后端提交 move
- `vue/src/components/dashboard/TodoColumn.vue` — 单列，包含 vuedraggable list；pending 列额外显示新增输入框
- `vue/src/components/dashboard/TodoCard.vue` — 单卡（标题、双击编辑、hover ✕）
- `vue/src/components/dashboard/RecentMedia.vue` — 拉 `/media?limit=12`，缩略图网格
- `vue/src/components/dashboard/StatsCard.vue` — 拉 `/api/dashboard/stats`，四个数字卡

**前端修改：**
- `vue/src/views/Dashboard.vue` — 完全重写为 dashboard 容器
- `vue/src/types.ts` — 增加 `Todo / TodoStatus / TodoBoard / DashboardStats`
- `vue/package.json` — 加 `vuedraggable@^4`

**文档：**
- `docs/dev_log/YYYY-MM-DD.md` 或现有日志文件追加一篇当日开发日志（按项目惯例）

---

## Task 1: 新增 Todo ORM 模型

**Files:**
- Create: `backend/app/models/todo.py`
- Modify: `backend/app/models/__init__.py`（在文件末尾追加 import）

- [ ] **Step 1: 创建 `Todo` 模型文件**

写入 `backend/app/models/todo.py`：

```python
from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime

from app.models import Base


class Todo(Base):
    __tablename__ = "todo"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    status = Column(String(16), nullable=False, default="pending", index=True)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_todo_status_position", "status", "position"),
    )
```

- [ ] **Step 2: 在 `models/__init__.py` 暴露 `Todo`**

在 `backend/app/models/__init__.py` 文件末尾（`def get_db()` 之后）追加：

```python

# 导入子模块模型，确保 Base.metadata 包含它们（alembic autogenerate 依赖此处）
from app.models.todo import Todo  # noqa: E402,F401
```

- [ ] **Step 3: 验证 import 不报错**

Run: `cd backend && python -c "from app.models import Todo; print(Todo.__tablename__)"`
Expected: `todo`

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/todo.py backend/app/models/__init__.py
git commit -m "feat(backend): 新增 Todo ORM 模型"
```

---

## Task 2: Alembic 迁移创建 todo 表

**Files:**
- Create: `backend/alembic/versions/20260429_<auto>_add_todo.py`（由 alembic 自动生成）

- [ ] **Step 1: 自动生成迁移文件**

Run: `cd backend && alembic revision --autogenerate -m "add_todo"`
Expected: 在 `backend/alembic/versions/` 下生成新文件，文件名形如 `20260429_HHMM_<rev>_add_todo.py`，路径打印到控制台。

- [ ] **Step 2: 检查迁移内容**

打开生成的迁移文件，确认 `upgrade()` 内仅包含 `op.create_table('todo', ...)` 与索引 `op.create_index('ix_todo_status_position', ...)` 和 `ix_todo_status`、`ix_todo_id`，没有意外的其他表 drop/alter。

如果 autogenerate 引入了无关变动（比如 drop 了某个不该 drop 的表），改写为只包含 todo 相关 op。

- [ ] **Step 3: 应用迁移**

Run: `cd backend && alembic upgrade head`
Expected: 输出最后一行包含 `Running upgrade ... -> <new_rev>, add_todo`，无报错。

- [ ] **Step 4: 验证表存在**

Run: `cd backend && python -c "from app.models import engine; from sqlalchemy import inspect; print(sorted(inspect(engine).get_table_names()))"`
Expected: 输出列表包含 `'todo'`。

- [ ] **Step 5: 提交**

```bash
git add backend/alembic/versions/
git commit -m "feat(backend): 添加 todo 表 alembic 迁移"
```

---

## Task 3: Todo Pydantic schemas

**Files:**
- Create: `backend/app/schemas/todo.py`

- [ ] **Step 1: 创建 schema 文件**

写入 `backend/app/schemas/todo.py`：

```python
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


TodoStatus = Literal["pending", "doing", "done"]


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    status: TodoStatus = "pending"


class TodoUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)


class TodoMove(BaseModel):
    status: TodoStatus
    position: int = Field(..., ge=0)


class TodoOut(BaseModel):
    id: int
    title: str
    status: TodoStatus
    position: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TodoBoard(BaseModel):
    pending: List[TodoOut]
    doing: List[TodoOut]
    done: List[TodoOut]
```

- [ ] **Step 2: 验证 import**

Run: `cd backend && python -c "from app.schemas.todo import TodoCreate, TodoMove, TodoBoard; print('ok')"`
Expected: `ok`

- [ ] **Step 3: 提交**

```bash
git add backend/app/schemas/todo.py
git commit -m "feat(backend): Todo Pydantic schemas"
```

---

## Task 4: Todo service 层（重排逻辑）

**Files:**
- Create: `backend/app/services/todo_service.py`

- [ ] **Step 1: 创建 service**

写入 `backend/app/services/todo_service.py`：

```python
"""Todo 看板列内/跨列移动的位置重排逻辑。

设计：把目标列（移动后）的有序列表算出来，再统一写回 0..N-1 的连续 position；
如果是跨列移动，源列把缺口压紧。这样无论拖到哪里都不会出现 position 空洞或冲突。
"""
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models import Todo
from app.schemas.todo import TodoStatus

DONE_LIMIT = 20  # 已完成列只展示最近 N 条


def list_board(db: Session) -> dict:
    """返回 {pending, doing, done}，前两列全量，done 仅最近 DONE_LIMIT 条。"""
    pending = (
        db.query(Todo).filter(Todo.status == "pending").order_by(Todo.position.asc()).all()
    )
    doing = (
        db.query(Todo).filter(Todo.status == "doing").order_by(Todo.position.asc()).all()
    )
    done = (
        db.query(Todo)
        .filter(Todo.status == "done")
        .order_by(Todo.completed_at.desc().nullslast(), Todo.id.desc())
        .limit(DONE_LIMIT)
        .all()
    )
    return {"pending": pending, "doing": doing, "done": done}


def _column(db: Session, status: TodoStatus) -> List[Todo]:
    return (
        db.query(Todo).filter(Todo.status == status).order_by(Todo.position.asc()).all()
    )


def _renumber(todos: List[Todo]) -> None:
    for i, t in enumerate(todos):
        if t.position != i:
            t.position = i


def create_todo(db: Session, title: str, status: TodoStatus = "pending") -> Todo:
    col = _column(db, status)
    todo = Todo(title=title, status=status, position=len(col))
    if status == "done":
        todo.completed_at = datetime.now()
    db.add(todo)
    db.flush()
    return todo


def move_todo(db: Session, todo: Todo, target_status: TodoStatus, target_pos: int) -> None:
    """将 todo 移到目标列的 target_pos 位置（0-based），原子重排两列 position。"""
    src_status = todo.status

    # 1. 取目标列（不含当前 todo）
    target_col = [t for t in _column(db, target_status) if t.id != todo.id]

    # 2. 钳制目标位置
    insert_at = max(0, min(target_pos, len(target_col)))

    # 3. 修改 todo 自身字段
    if target_status == "done" and src_status != "done":
        todo.completed_at = datetime.now()
    elif target_status != "done" and src_status == "done":
        todo.completed_at = None
    todo.status = target_status

    # 4. 把 todo 插入目标列指定位置
    target_col.insert(insert_at, todo)
    _renumber(target_col)

    # 5. 如果跨列，源列重新压紧
    if src_status != target_status:
        src_col = [t for t in _column(db, src_status) if t.id != todo.id]
        _renumber(src_col)


def update_title(db: Session, todo: Todo, title: str) -> None:
    todo.title = title


def delete_todo(db: Session, todo: Todo) -> None:
    """物理删除并压紧所在列 position。"""
    status = todo.status
    db.delete(todo)
    db.flush()
    col = _column(db, status)
    _renumber(col)
```

- [ ] **Step 2: 验证 import**

Run: `cd backend && python -c "from app.services.todo_service import list_board, move_todo; print('ok')"`
Expected: `ok`

- [ ] **Step 3: 烟测重排逻辑（手写脚本）**

Run（在仓库根目录）：
```bash
cd backend && python -c "
from app.models import SessionLocal, Todo
from app.services.todo_service import create_todo, move_todo, list_board
db = SessionLocal()
# 清理可能的残留
db.query(Todo).delete(); db.commit()
a = create_todo(db, 'A')
b = create_todo(db, 'B')
c = create_todo(db, 'C')
db.commit()
# 把 C 移到 doing 列首
move_todo(db, c, 'doing', 0)
db.commit()
# 把 A 拖到 pending 列末（同列向后）
move_todo(db, a, 'pending', 99)
db.commit()
board = list_board(db)
print('pending:', [(t.title, t.position) for t in board['pending']])
print('doing:', [(t.title, t.position) for t in board['doing']])
print('done:', [(t.title, t.position) for t in board['done']])
db.query(Todo).delete(); db.commit()
"
```

Expected:
```
pending: [('B', 0), ('A', 1)]
doing: [('C', 0)]
done: []
```

如果输出不符（比如 position 不是 0/1 连续，或顺序错），回到 Step 1 修 service 再跑。

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/todo_service.py
git commit -m "feat(backend): Todo 看板列内/跨列移动 service"
```

---

## Task 5: Todo 路由

**Files:**
- Create: `backend/app/routers/todos.py`
- Modify: `backend/app/routers/__init__.py`

- [ ] **Step 1: 创建路由**

写入 `backend/app/routers/todos.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Todo, get_db
from app.schemas.todo import (
    TodoBoard,
    TodoCreate,
    TodoMove,
    TodoOut,
    TodoUpdate,
)
from app.services import todo_service

router = APIRouter(prefix="/todos", tags=["todos"])


def _get(db: Session, todo_id: int) -> Todo:
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="todo not found")
    return todo


@router.get("", response_model=TodoBoard)
def get_board(db: Session = Depends(get_db)):
    return todo_service.list_board(db)


@router.post("", response_model=TodoOut, status_code=201)
def create(payload: TodoCreate, db: Session = Depends(get_db)):
    todo = todo_service.create_todo(db, payload.title, payload.status)
    db.commit()
    db.refresh(todo)
    return todo


@router.patch("/{todo_id}", response_model=TodoOut)
def update_title(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)):
    todo = _get(db, todo_id)
    todo_service.update_title(db, todo, payload.title)
    db.commit()
    db.refresh(todo)
    return todo


@router.patch("/{todo_id}/move", response_model=TodoOut)
def move(todo_id: int, payload: TodoMove, db: Session = Depends(get_db)):
    todo = _get(db, todo_id)
    todo_service.move_todo(db, todo, payload.status, payload.position)
    db.commit()
    db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=204)
def delete(todo_id: int, db: Session = Depends(get_db)):
    todo = _get(db, todo_id)
    todo_service.delete_todo(db, todo)
    db.commit()
```

- [ ] **Step 2: 注册路由**

修改 `backend/app/routers/__init__.py`，在 import 段最后追加 `from .todos import router as todos_router`，并在 `all_routers` 列表里追加 `todos_router`。完整文件应为：

```python
from .actor import router as actor_router
from .message import router as message_router
from .media import router as media_router
from .files import router as files_router
from .tags import router as tags_router
from .sync import router as sync_router
from .admin import router as admin_router
from .dashboard import router as dashboard_router
from .todos import router as todos_router

# 所有路由列表
all_routers = [
    actor_router,
    message_router,
    media_router,
    files_router,
    tags_router,
    sync_router,
    admin_router,
    dashboard_router,
    todos_router,
]
```

- [ ] **Step 3: 启动后端并冒烟**

打开一个终端运行 `cd backend && python api.py`，然后另开一个终端：

```bash
curl -s -X POST http://127.0.0.1:8002/todos -H "Content-Type: application/json" -d '{"title":"hello"}'
curl -s http://127.0.0.1:8002/todos | python -m json.tool
curl -s -X PATCH http://127.0.0.1:8002/todos/1/move -H "Content-Type: application/json" -d '{"status":"doing","position":0}'
curl -s http://127.0.0.1:8002/todos | python -m json.tool
curl -s -X DELETE -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8002/todos/1
```

Expected：
- 第一次 POST 返回带 `id`、`status:"pending"`、`position:0` 的 JSON。
- 第一次 GET 看到 `pending` 列里有该 todo。
- PATCH move 后 `status:"doing"`、`position:0`。
- 第二次 GET 该 todo 出现在 `doing` 列，`pending` 列空。
- DELETE 返回 `204`。

- [ ] **Step 4: 停掉后端，提交**

```bash
git add backend/app/routers/todos.py backend/app/routers/__init__.py
git commit -m "feat(backend): /todos 路由"
```

---

## Task 6: 替换 dashboard router — 删除 markdown 端点，加 stats

**Files:**
- Modify: `backend/app/routers/dashboard.py`（重写为只剩 stats）
- Modify: `backend/app/config.py`（清除未用常量/方法）

- [ ] **Step 1: 检查 markdown 端点引用**

Run: `grep -rn "DASHBOARD_DEFAULT_CONTENT\|get_dashboard_md_path\|/api/dashboard" backend vue 2>&1`
Expected: 列出引用位置；预期只在 `backend/app/config.py`、`backend/app/routers/dashboard.py`、`vue/src/views/Dashboard.vue` 三处。如果有别的位置（比如 admin 工具引用），把那里也加入本任务的清理清单。

- [ ] **Step 2: 重写 dashboard.py**

完整覆盖 `backend/app/routers/dashboard.py`：

```python
"""主页 dashboard 聚合统计端点。"""
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Media, Message, Todo, get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    message_count: int
    media_count: int
    media_this_month: int
    todo_doing_count: int


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)) -> DashboardStats:
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    return DashboardStats(
        message_count=db.query(func.count(Message.id)).scalar() or 0,
        media_count=db.query(func.count(Media.id)).scalar() or 0,
        media_this_month=db.query(func.count(Media.id))
        .filter(Media.created_at >= month_start)
        .scalar()
        or 0,
        todo_doing_count=db.query(func.count(Todo.id))
        .filter(Todo.status == "doing")
        .scalar()
        or 0,
    )
```

- [ ] **Step 3: 清理 config.py 中孤儿引用**

打开 `backend/app/config.py`，删除：
- `DASHBOARD_DEFAULT_CONTENT` 常量定义
- `get_dashboard_md_path` 方法定义
- 任何只为它们存在的 import / 子目录创建逻辑

如果 `get_static_mounts()` 或 `check_mount_names()` 列表里包含 dashboard markdown 文件目录，保留挂载（用户文件可能仍在那里），仅删除常量与方法。

如不确定，运行 `grep -n "dashboard" backend/app/config.py` 列出残留引用，把无人调用的逐一删除。

- [ ] **Step 4: 验证后端启动 + stats 端点**

启动后端 `cd backend && python api.py`，另开终端：

```bash
curl -s http://127.0.0.1:8002/api/dashboard/stats | python -m json.tool
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8002/api/dashboard
```

Expected：
- 第一条返回 4 个字段都是非负整数的 JSON。
- 第二条返回 `404`（旧 markdown GET 已删除）。

- [ ] **Step 5: 停后端，提交**

```bash
git add backend/app/routers/dashboard.py backend/app/config.py
git commit -m "feat(backend): dashboard 路由替换为 stats 聚合端点"
```

---

## Task 7: 前端类型与依赖

**Files:**
- Modify: `vue/src/types.ts`
- Modify: `vue/package.json`（通过 pnpm add）

- [ ] **Step 1: 安装 vuedraggable**

Run: `cd vue && pnpm add vuedraggable@^4`
Expected: `package.json` `dependencies` 中出现 `"vuedraggable": "^4.x.x"`，无安装错误。

- [ ] **Step 2: 添加类型**

打开 `vue/src/types.ts`，在文件末尾追加：

```ts
// ---------------------------------------------------------------------------
// Dashboard / Todo
// ---------------------------------------------------------------------------

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
  doing: Todo[]
  done: Todo[]
}

export interface DashboardStats {
  message_count: number
  media_count: number
  media_this_month: number
  todo_doing_count: number
}
```

- [ ] **Step 3: 类型检查**

Run: `cd vue && pnpm exec vue-tsc --noEmit`
Expected: 无错误（如果有错误且与本次新增无关，记录但继续；如果与新增类型有关，修复）。

- [ ] **Step 4: 提交**

```bash
git add vue/package.json vue/pnpm-lock.yaml vue/src/types.ts
git commit -m "feat(vue): vuedraggable 依赖 + Dashboard/Todo 类型"
```

---

## Task 8: TodoCard 组件

**Files:**
- Create: `vue/src/components/dashboard/TodoCard.vue`

- [ ] **Step 1: 创建组件**

写入 `vue/src/components/dashboard/TodoCard.vue`：

```vue
<template>
  <div
    class="group bg-white dark:bg-gray-800 border border-[var(--border-color)] rounded-lg px-3 py-2 shadow-sm hover:shadow transition-shadow cursor-grab active:cursor-grabbing"
  >
    <div v-if="!editing" class="flex items-start gap-2">
      <span
        @dblclick="startEdit"
        class="flex-1 text-sm text-gray-900 dark:text-gray-100 break-words select-none"
        :class="{ 'line-through text-gray-400 dark:text-gray-500': todo.status === 'done' }"
      >
        {{ todo.title }}
      </span>
      <button
        @click="$emit('delete', todo)"
        class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 text-sm leading-none transition-opacity"
        title="删除"
      >
        ✕
      </button>
    </div>
    <input
      v-else
      ref="inputRef"
      v-model="draft"
      @keydown.enter.prevent="commit"
      @keydown.esc.prevent="cancel"
      @blur="commit"
      class="w-full text-sm bg-transparent border-b border-[var(--color-primary-500)] text-gray-900 dark:text-gray-100 focus:outline-none"
    />
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import type { Todo } from '../../types'

const props = defineProps<{ todo: Todo }>()
const emit = defineEmits<{
  rename: [todo: Todo, title: string]
  delete: [todo: Todo]
}>()

const editing = ref(false)
const draft = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

function startEdit() {
  draft.value = props.todo.title
  editing.value = true
  nextTick(() => inputRef.value?.focus())
}

function commit() {
  if (!editing.value) return
  const title = draft.value.trim()
  editing.value = false
  if (title && title !== props.todo.title) {
    emit('rename', props.todo, title)
  }
}

function cancel() {
  editing.value = false
}
</script>
```

- [ ] **Step 2: 类型检查**

Run: `cd vue && pnpm exec vue-tsc --noEmit`
Expected: 无新增错误。

- [ ] **Step 3: 提交**

```bash
git add vue/src/components/dashboard/TodoCard.vue
git commit -m "feat(vue): TodoCard 组件"
```

---

## Task 9: TodoColumn 组件

**Files:**
- Create: `vue/src/components/dashboard/TodoColumn.vue`

- [ ] **Step 1: 创建组件**

写入 `vue/src/components/dashboard/TodoColumn.vue`：

```vue
<template>
  <div class="flex flex-col bg-white/40 dark:bg-black/20 border border-[var(--border-color)] rounded-xl p-3 min-h-[200px]">
    <div class="flex items-center justify-between mb-2 px-1">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200">
        {{ title }}
        <span class="ml-1 text-xs text-gray-400">{{ todos.length }}</span>
      </h3>
    </div>

    <draggable
      :list="todos"
      group="todos"
      :animation="150"
      item-key="id"
      ghost-class="opacity-40"
      class="flex-1 flex flex-col gap-2 min-h-[40px]"
      @change="onChange"
    >
      <template #item="{ element }">
        <TodoCard
          :todo="element"
          @rename="(t, title) => $emit('rename', t, title)"
          @delete="(t) => $emit('delete', t)"
        />
      </template>
    </draggable>

    <form
      v-if="status === 'pending'"
      @submit.prevent="addNew"
      class="mt-2"
    >
      <input
        v-model="newTitle"
        placeholder="+ 新增待办，回车提交"
        class="w-full text-sm bg-transparent border border-dashed border-[var(--border-color)] rounded-md px-2 py-1.5 text-gray-700 dark:text-gray-200 placeholder:text-gray-400 focus:outline-none focus:border-[var(--color-primary-500)]"
      />
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import draggable from 'vuedraggable'
import TodoCard from './TodoCard.vue'
import type { Todo, TodoStatus } from '../../types'

defineProps<{
  status: TodoStatus
  title: string
  todos: Todo[]
}>()

const emit = defineEmits<{
  add: [title: string]
  rename: [todo: Todo, title: string]
  delete: [todo: Todo]
  // vuedraggable change 事件透传给父级
  changed: [event: { added?: { element: Todo; newIndex: number }, moved?: { element: Todo; newIndex: number, oldIndex: number } }]
}>()

const newTitle = ref('')

function addNew() {
  const t = newTitle.value.trim()
  if (!t) return
  newTitle.value = ''
  emit('add', t)
}

function onChange(event: any) {
  emit('changed', event)
}
</script>
```

- [ ] **Step 2: 类型检查**

Run: `cd vue && pnpm exec vue-tsc --noEmit`
Expected: 无新增错误。如出现 `vuedraggable` 类型缺失警告，可在新建文件 `vue/src/types/vuedraggable.d.ts` 内写 `declare module 'vuedraggable'`，把它纳入本任务。

- [ ] **Step 3: 提交**

```bash
git add vue/src/components/dashboard/TodoColumn.vue vue/src/types/vuedraggable.d.ts 2>/dev/null || git add vue/src/components/dashboard/TodoColumn.vue
git commit -m "feat(vue): TodoColumn 组件"
```

---

## Task 10: TodoBoard 容器（拖拽 + API 调用）

**Files:**
- Create: `vue/src/components/dashboard/TodoBoard.vue`

- [ ] **Step 1: 创建组件**

写入 `vue/src/components/dashboard/TodoBoard.vue`：

```vue
<template>
  <section class="bg-white/30 dark:bg-black/20 backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-base font-bold text-gray-900 dark:text-white">📋 Todo 看板</h2>
      <button
        v-if="!loading"
        @click="reload"
        class="text-xs text-gray-500 dark:text-gray-400 hover:text-[var(--color-primary-500)]"
        title="刷新"
      >
        ↻
      </button>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">加载中…</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <TodoColumn
        status="pending"
        title="待办"
        :todos="board.pending"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('pending', e)"
      />
      <TodoColumn
        status="doing"
        title="进行中"
        :todos="board.doing"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('doing', e)"
      />
      <TodoColumn
        status="done"
        title="已完成"
        :todos="board.done"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('done', e)"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'
import { useConfirm } from '../../composables/useConfirm'
import TodoColumn from './TodoColumn.vue'
import type { Todo, TodoBoard as TodoBoardData, TodoStatus } from '../../types'

const toast = useToast()
const confirm = useConfirm()

const loading = ref(true)
const board = reactive<TodoBoardData>({ pending: [], doing: [], done: [] })

async function reload() {
  loading.value = true
  try {
    const data = await api.get<TodoBoardData>('/todos')
    board.pending = data.pending
    board.doing = data.doing
    board.done = data.done
  } catch (e) {
    toast.error(`加载 Todo 失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
}

async function handleAdd(title: string) {
  try {
    const created = await api.post<Todo>('/todos', { title })
    board.pending.push(created)
  } catch (e) {
    toast.error(`新增失败：${(e as Error).message}`)
  }
}

async function handleRename(todo: Todo, title: string) {
  const original = todo.title
  todo.title = title  // 乐观
  try {
    await api.patch<Todo>(`/todos/${todo.id}`, { title })
  } catch (e) {
    todo.title = original
    toast.error(`修改失败：${(e as Error).message}`)
  }
}

async function handleDelete(todo: Todo) {
  const ok = await confirm({ title: '删除', message: `确定删除「${todo.title}」？` })
  if (!ok) return
  try {
    await api.del(`/todos/${todo.id}`)
    await reload()  // 删除后重排，简单处理
  } catch (e) {
    toast.error(`删除失败：${(e as Error).message}`)
  }
}

async function onChange(status: TodoStatus, event: any) {
  const item: Todo | undefined = event.added?.element ?? event.moved?.element
  const newIndex: number | undefined = event.added?.newIndex ?? event.moved?.newIndex
  if (!item || newIndex === undefined) return
  try {
    await api.patch<Todo>(`/todos/${item.id}/move`, { status, position: newIndex })
  } catch (e) {
    toast.error(`移动失败：${(e as Error).message}`)
    await reload()  // 回滚
  }
}

onMounted(reload)
</script>
```

注意：上面引用了 `useConfirm`，仓库里已存在 `vue/src/composables/useConfirm.ts`。如签名不同（如返回值不是布尔 Promise），按现有 API 适配 `handleDelete`，必要时回退到 `window.confirm`。

- [ ] **Step 2: 检查 useConfirm 接口**

Run: `head -40 vue/src/composables/useConfirm.ts`
若 API 与本任务假设的 `confirm({title, message}) => Promise<boolean>` 不同，调整 `handleDelete` 中的调用方式。

- [ ] **Step 3: 类型检查**

Run: `cd vue && pnpm exec vue-tsc --noEmit`
Expected: 无新增错误。

- [ ] **Step 4: 提交**

```bash
git add vue/src/components/dashboard/TodoBoard.vue
git commit -m "feat(vue): TodoBoard 容器（拖拽 + API）"
```

---

## Task 11: RecentMedia 组件

**Files:**
- Create: `vue/src/components/dashboard/RecentMedia.vue`

- [ ] **Step 1: 检查现有 media list 响应结构**

Run: `grep -n "thumb_url\|/media" vue/src/types.ts | head -20`
确认 `Media` 类型字段名（`thumb_url`、`id`、`mime_type` 等）。下面组件中如字段名与实际不符，按实际为准。

- [ ] **Step 2: 创建组件**

写入 `vue/src/components/dashboard/RecentMedia.vue`：

```vue
<template>
  <section class="bg-white/30 dark:bg-black/20 backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-base font-bold text-gray-900 dark:text-white">🖼️ 最近媒体</h2>
      <router-link to="/media" class="text-xs text-gray-500 hover:text-[var(--color-primary-500)]">查看全部 →</router-link>
    </div>
    <div v-if="loading" class="text-center py-6 text-gray-500 text-sm">加载中…</div>
    <div v-else-if="!items.length" class="text-center py-6 text-gray-400 text-sm italic">暂无媒体</div>
    <div v-else class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2">
      <router-link
        v-for="m in items"
        :key="m.id"
        :to="`/media/${m.id}`"
        class="aspect-square overflow-hidden rounded-lg bg-gray-200 dark:bg-gray-700 hover:ring-2 hover:ring-[var(--color-primary-500)] transition"
      >
        <img
          :src="m.thumb_url"
          :alt="`media-${m.id}`"
          class="w-full h-full object-cover"
          loading="lazy"
        />
      </router-link>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'

interface MediaThumb {
  id: number
  thumb_url: string
}

interface CursorResponse<T> {
  items: T[]
  next_cursor: string | null
  has_more: boolean
}

const toast = useToast()
const loading = ref(true)
const items = ref<MediaThumb[]>([])

onMounted(async () => {
  try {
    const data = await api.get<CursorResponse<MediaThumb>>('/media', { limit: 12 })
    items.value = data.items
  } catch (e) {
    toast.error(`加载最近媒体失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})
</script>
```

注意：`api.get` 第二参数是否支持 query 参数对象，若不支持，改写成 `api.get('/media?limit=12')`。先看一眼 `vue/src/composables/useApi.ts` 中 get 的签名再下手。

- [ ] **Step 3: 验证媒体列表 endpoint 与字段**

Run: `curl -s "http://127.0.0.1:8002/media?limit=2" | python -m json.tool | head -30`（先启动后端）
看返回 JSON 中 item 字段是否含 `thumb_url`、`id`。如不同，调整组件类型。

- [ ] **Step 4: 类型检查**

Run: `cd vue && pnpm exec vue-tsc --noEmit`
Expected: 无新增错误。

- [ ] **Step 5: 提交**

```bash
git add vue/src/components/dashboard/RecentMedia.vue
git commit -m "feat(vue): RecentMedia 组件"
```

---

## Task 12: StatsCard 组件

**Files:**
- Create: `vue/src/components/dashboard/StatsCard.vue`

- [ ] **Step 1: 创建组件**

写入 `vue/src/components/dashboard/StatsCard.vue`：

```vue
<template>
  <section class="bg-white/30 dark:bg-black/20 backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
    <h2 class="text-base font-bold text-gray-900 dark:text-white mb-3">📊 统计</h2>
    <div v-if="loading" class="text-center py-4 text-gray-500 text-sm">加载中…</div>
    <div v-else class="grid grid-cols-2 gap-3">
      <Stat label="消息总数" :value="stats.message_count" />
      <Stat label="媒体总数" :value="stats.media_count" />
      <Stat label="本月新增媒体" :value="stats.media_this_month" />
      <Stat label="进行中 Todo" :value="stats.todo_doing_count" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { h, onMounted, ref, defineComponent } from 'vue'
import { api } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'
import type { DashboardStats } from '../../types'

const Stat = defineComponent({
  props: { label: { type: String, required: true }, value: { type: Number, required: true } },
  setup(props) {
    return () =>
      h('div', { class: 'rounded-lg border border-[var(--border-color)] bg-white/50 dark:bg-gray-800/50 p-3' }, [
        h('div', { class: 'text-2xl font-bold text-gray-900 dark:text-white' }, String(props.value)),
        h('div', { class: 'text-xs text-gray-500 dark:text-gray-400 mt-1' }, props.label),
      ])
  },
})

const toast = useToast()
const loading = ref(true)
const stats = ref<DashboardStats>({
  message_count: 0,
  media_count: 0,
  media_this_month: 0,
  todo_doing_count: 0,
})

onMounted(async () => {
  try {
    stats.value = await api.get<DashboardStats>('/api/dashboard/stats')
  } catch (e) {
    toast.error(`加载统计失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})
</script>
```

- [ ] **Step 2: 类型检查**

Run: `cd vue && pnpm exec vue-tsc --noEmit`
Expected: 无新增错误。

- [ ] **Step 3: 提交**

```bash
git add vue/src/components/dashboard/StatsCard.vue
git commit -m "feat(vue): StatsCard 组件"
```

---

## Task 13: 重写 Dashboard.vue 视图

**Files:**
- Modify: `vue/src/views/Dashboard.vue`（完全替换）

- [ ] **Step 1: 完全覆盖文件内容**

写入 `vue/src/views/Dashboard.vue`：

```vue
<template>
  <div class="min-h-screen pb-24 md:pb-8">
    <div class="max-w-7xl w-full mx-auto px-4 pt-6 space-y-4">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">主页</h1>

      <TodoBoard />

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="lg:col-span-2">
          <RecentMedia />
        </div>
        <div>
          <StatsCard />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import TodoBoard from '../components/dashboard/TodoBoard.vue'
import RecentMedia from '../components/dashboard/RecentMedia.vue'
import StatsCard from '../components/dashboard/StatsCard.vue'
</script>
```

- [ ] **Step 2: 删除遗留 markdown 加载相关 import 检查**

Run: `grep -n "renderMarkdown\|/api/dashboard\b" vue/src 2>&1 | head`
Expected: 仅 `StatsCard.vue` 中 `/api/dashboard/stats` 出现，不再有 `renderMarkdown` 来自旧 Dashboard 的引用。如其他地方仍引用 `/api/dashboard` GET 旧端点，删之。

- [ ] **Step 3: 启动并手测**

启动后端 `cd backend && python api.py`，启动前端 `cd vue && pnpm dev`，浏览器开 `http://localhost:5173/`：

1. 看到 Todo 看板（三列：待办 / 进行中 / 已完成）+ 最近媒体九宫格 + 统计四卡，无控制台报错。
2. 在「待办」列底部输入"测试 todo 1"回车 → 出现在待办列。
3. 把"测试 todo 1"拖到"进行中"列 → 状态切换；刷新页面后仍在进行中列。
4. 双击"测试 todo 1"，改名"测试 todo 1b"，回车 → 标题更新；刷新后保持。
5. 拖到"已完成"列 → 文本带删除线；刷新后仍在已完成列。
6. hover 卡片，点 ✕ → 弹出确认；确认后消失。
7. 统计卡四项均为非负数；最近媒体若数据库有媒体则显示缩略图，点击缩略图跳到 `/media/:id`。

如任一步骤异常，先看浏览器控制台 + 后端日志（`backend/logs/app.log`），定位失败接口/字段后回到对应 Task 修。

- [ ] **Step 4: 类型检查 + 构建**

Run: `cd vue && pnpm build`
Expected: 编译完成，无错误。

- [ ] **Step 5: 提交**

```bash
git add vue/src/views/Dashboard.vue
git commit -m "feat(vue): Dashboard 主页改造为 widget 容器"
```

---

## Task 14: 清理与开发日志

**Files:**
- Modify: 可能的孤儿文件（用户的旧 dashboard.md 内容文件夹），CLAUDE.md（如果引用了 markdown 主页）
- Create / Modify: `docs/dev_log/<latest>.md`

- [ ] **Step 1: 找孤儿引用**

Run（仓库根）：
```bash
grep -rn "dashboard.md\|DASHBOARD_DEFAULT_CONTENT\|get_dashboard_md_path\|renderMarkdown.*Dashboard" backend vue CLAUDE.md 2>&1 | head -30
```
Expected: 输出为空或仅命中本任务待清理项。把仍存在的引用删掉。

- [ ] **Step 2: 检查 CLAUDE.md 是否描述了旧主页**

Run: `grep -n -i "markdown\|主页\|dashboard" CLAUDE.md`
若行内描述"主页是 Markdown 文件"等已过时句子，更新为"主页是 widget 容器（Todo 看板 / 最近媒体 / 统计）"。

- [ ] **Step 3: 写开发日志**

按项目惯例（用户全局规则：每次添加功能或修复 bug 后写开发日志，每天一篇）：

Run: `ls docs/dev_log/ 2>/dev/null || ls docs/ 2>&1 | head`
找到现有日志位置，今天日期文件存在则追加章节，不存在则新建 `docs/dev_log/2026-04-29.md`，写入：

```markdown
# 2026-04-29 开发日志

## 主页 Dashboard + Todo 看板

**动机：** 旧主页是只读 Markdown，每次完成 todo 都要编辑文本，太笨重。

**改动：**
- 新建 `Todo` 表 + `/todos` 路由（GET 看板 / POST 新建 / PATCH 改标题 / PATCH /move 移动 / DELETE）。Service 层 `todo_service.py` 处理同列/跨列移动的位置重排，确保 position 始终连续 0..N-1。
- `dashboard.py` 路由替换：删除 markdown 文件 GET/PUT；新增 `GET /api/dashboard/stats` 聚合消息数 / 媒体数 / 本月新增媒体 / 进行中 Todo。
- 前端 `views/Dashboard.vue` 重写为 widget 容器：`TodoBoard`（vuedraggable 三列拖拽）+ `RecentMedia`（九宫格缩略图）+ `StatsCard`（四个数字卡）。
- 已完成列只展示最近 20 条（`DONE_LIMIT` in `todo_service.py`）。

**坑：**
- 此处可在实施过程中补充实际遇到的坑（如 alembic autogenerate 多生成内容、vuedraggable 类型缺失等）。
```

实际写入时把"坑"段替换成实施过程中真正遇到的问题；如未遇到则删除该段。

- [ ] **Step 4: 提交**

```bash
git add docs/dev_log/ CLAUDE.md
git commit -m "docs: 主页 dashboard 开发日志 + 文档清理"
```

---

## 自检覆盖清单

| Spec 要求 | 实现于 |
|---|---|
| Todo 表 title/status/position/created_at/updated_at/completed_at | Task 1, 2 |
| GET /todos 三列分组，done 限 20 | Task 4, 5 |
| POST /todos 新增 | Task 5 |
| PATCH /todos/{id} 改标题 | Task 5 |
| PATCH /todos/{id}/move 跨列重排 + completed_at 处理 | Task 4, 5 |
| DELETE /todos/{id} | Task 5 |
| GET /stats 聚合 4 个指标 | Task 6 |
| 跨列拖拽 + 同列排序（vuedraggable） | Task 9, 10 |
| 双击编辑 / hover 删除 | Task 8, 10 |
| pending 列底部新增输入框 | Task 9 |
| 乐观更新 + 失败 toast + reload 回滚 | Task 10 |
| 固定网格布局：Todo 整宽 + 下行 RecentMedia(2/3) + StatsCard(1/3) | Task 13 |
| 完全替换旧 Markdown 主页 | Task 6, 13, 14 |
| 开发日志 | Task 14 |
