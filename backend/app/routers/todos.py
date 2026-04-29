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
