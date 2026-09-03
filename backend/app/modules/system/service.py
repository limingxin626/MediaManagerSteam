"""Cross-domain reporting queries."""
import os
from datetime import datetime, timedelta
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from app.config import config
from app.models import Collection, Media, Message, MessageMedia, Person, SyncLog, Tag, Todo
from app.modules.system.schemas import DashboardStats, HeatmapDay, HeatmapResponse


def dashboard_stats(db: Session) -> DashboardStats:
    now = datetime.now(); month_start = datetime(now.year, now.month, 1)
    return DashboardStats(message_count=db.query(func.count(Message.id)).scalar() or 0, media_count=db.query(func.count(Media.id)).scalar() or 0, media_this_month=db.query(func.count(Media.id)).filter(Media.created_at >= month_start).scalar() or 0, todo_doing_count=db.query(func.count(Todo.id)).filter(Todo.status == "doing").scalar() or 0)


def heatmap(db: Session) -> HeatmapResponse:
    today = datetime.now().date(); start = today - timedelta(days=364)
    date_label = func.strftime('%Y-%m-%d', Message.created_at).label('date_str')
    rows = db.query(date_label, func.count().label('cnt')).filter(Message.created_at >= datetime.combine(start, datetime.min.time())).group_by(date_label).all()
    counts = {row.date_str: row.cnt for row in rows}
    days = [HeatmapDay(date=(start + timedelta(days=i)).isoformat(), count=counts.get((start + timedelta(days=i)).isoformat(), 0)) for i in range(365)]
    return HeatmapResponse(start_date=start.isoformat(), end_date=today.isoformat(), days=days)


def admin_stats(db: Session) -> dict:
    table_counts = {"message": db.query(func.count(Message.id)).scalar() or 0, "media": db.query(func.count(Media.id)).scalar() or 0, "collection": db.query(func.count(Collection.id)).scalar() or 0, "person": db.query(func.count(Person.id)).scalar() or 0, "tag": db.query(func.count(Tag.id)).scalar() or 0, "message_media": db.query(func.count(MessageMedia.message_id)).scalar() or 0, "message_tag": db.scalar(text("SELECT COUNT(*) FROM message_tag")) or 0, "media_person": db.scalar(text("SELECT COUNT(*) FROM media_person")) or 0, "sync_log": db.query(func.count(SyncLog.id)).scalar() or 0}
    storage = db.query(func.count(Media.id), func.coalesce(func.sum(Media.file_size), 0)).one()
    recent = db.query(Message.id, Message.text, Message.collection_id, Message.created_at).order_by(Message.created_at.desc()).limit(10).all()
    db_path = config.get_db_path()
    return {"table_counts": table_counts, "storage": {"total_files": storage[0], "total_size": storage[1]}, "db_size": os.path.getsize(db_path) if os.path.exists(db_path) else 0, "recent_messages": [{"id": row.id, "text": row.text, "collection_id": row.collection_id, "created_at": row.created_at.isoformat() if row.created_at else None} for row in recent]}


def sync_logs(db: Session, cursor: str | None, limit: int, entity_type: str | None) -> dict:
    query = db.query(SyncLog).order_by(SyncLog.timestamp.desc(), SyncLog.id.desc())
    if entity_type: query = query.filter(SyncLog.entity_type == entity_type)
    if cursor:
        raw_time, raw_id = cursor.split("|", 1); timestamp = datetime.fromisoformat(raw_time); item_id = int(raw_id)
        query = query.filter((SyncLog.timestamp < timestamp) | ((SyncLog.timestamp == timestamp) & (SyncLog.id < item_id)))
    rows = query.limit(limit + 1).all(); has_more = len(rows) > limit; items = rows[:limit]
    last = items[-1] if has_more and items else None
    return {"items": [{"id": row.id, "entity_type": row.entity_type, "entity_id": row.entity_id, "operation": row.operation, "timestamp": row.timestamp.isoformat() if row.timestamp else None} for row in items], "next_cursor": f"{last.timestamp.isoformat()}|{last.id}" if last else None, "has_more": has_more}
