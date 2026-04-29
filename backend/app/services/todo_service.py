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
