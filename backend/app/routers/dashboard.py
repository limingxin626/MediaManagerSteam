"""主页 dashboard 聚合统计端点。"""
from datetime import datetime, timedelta
from typing import List
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


class HeatmapDay(BaseModel):
    date: str
    count: int


class HeatmapResponse(BaseModel):
    start_date: str
    end_date: str
    days: List[HeatmapDay]


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


@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(db: Session = Depends(get_db)) -> HeatmapResponse:
    """过去 365 天每日消息数（GitHub 风格热力图）。"""
    today = datetime.now().date()
    start = today - timedelta(days=364)
    start_dt = datetime.combine(start, datetime.min.time())

    date_label = func.strftime('%Y-%m-%d', Message.created_at).label('date_str')
    rows = (
        db.query(date_label, func.count().label('cnt'))
        .filter(Message.created_at >= start_dt)
        .group_by(date_label)
        .all()
    )
    counts = {row.date_str: row.cnt for row in rows}
    days = [
        HeatmapDay(
            date=(start + timedelta(days=i)).isoformat(),
            count=counts.get((start + timedelta(days=i)).isoformat(), 0),
        )
        for i in range(365)
    ]
    return HeatmapResponse(start_date=start.isoformat(), end_date=today.isoformat(), days=days)
