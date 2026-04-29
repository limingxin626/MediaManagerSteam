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
