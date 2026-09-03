from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db
from app.modules.todo.schemas import (
    TodoBoard,
    TodoCreate,
    TodoMove,
    TodoOut,
    TodoUpdate,
)
from app.modules.todo import service as todo_service

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=TodoBoard)
def get_board(db: Session = Depends(get_db)):
    return todo_service.list_board(db)


@router.post("", response_model=TodoOut, status_code=201)
def create(payload: TodoCreate, db: Session = Depends(get_db)):
    return todo_service.create_use_case(db, payload.title, payload.status)


@router.patch("/{todo_id}", response_model=TodoOut)
def update_title(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)):
    try: return todo_service.update_use_case(db, todo_id, payload.title)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{todo_id}/move", response_model=TodoOut)
def move(todo_id: int, payload: TodoMove, db: Session = Depends(get_db)):
    try: return todo_service.move_use_case(db, todo_id, payload.status, payload.position)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{todo_id}", status_code=204)
def delete(todo_id: int, db: Session = Depends(get_db)):
    try: todo_service.delete_use_case(db, todo_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
