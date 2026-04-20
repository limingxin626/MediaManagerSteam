import os

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.config import config
from app.models import get_db, Message, Media, Actor, Tag, MessageMedia, SyncLog, message_tag

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    table_counts = {
        "message": db.query(func.count(Message.id)).scalar() or 0,
        "media": db.query(func.count(Media.id)).scalar() or 0,
        "actor": db.query(func.count(Actor.id)).scalar() or 0,
        "tag": db.query(func.count(Tag.id)).scalar() or 0,
        "message_media": db.query(func.count(MessageMedia.message_id)).scalar() or 0,
        "message_tag": db.scalar(text("SELECT COUNT(*) FROM message_tag")) or 0,
        "sync_log": db.query(func.count(SyncLog.id)).scalar() or 0,
    }

    storage_row = db.query(
        func.count(Media.id).label("total_files"),
        func.coalesce(func.sum(Media.file_size), 0).label("total_size"),
    ).one()

    db_path = config.get_db_path()
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    recent = (
        db.query(Message.id, Message.text, Message.actor_id, Message.created_at)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "table_counts": table_counts,
        "storage": {
            "total_files": storage_row.total_files,
            "total_size": storage_row.total_size,
        },
        "db_size": db_size,
        "recent_messages": [
            {
                "id": r.id,
                "text": r.text,
                "actor_id": r.actor_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent
        ],
    }


@router.get("/sync-logs")
def get_sync_logs(
    cursor: str | None = Query(None, description="分页游标 (ISO datetime)"),
    limit: int = Query(20, ge=1, le=100),
    entity_type: str | None = Query(None, description="按实体类型筛选"),
    db: Session = Depends(get_db),
):
    """游标分页浏览 sync_log 表。"""
    query = db.query(SyncLog).order_by(SyncLog.timestamp.desc(), SyncLog.id.desc())

    if entity_type:
        query = query.filter(SyncLog.entity_type == entity_type)

    if cursor:
        # 游标格式: "timestamp|id"
        parts = cursor.split("|")
        if len(parts) == 2:
            from datetime import datetime
            ts = datetime.fromisoformat(parts[0])
            cid = int(parts[1])
            query = query.filter(
                (SyncLog.timestamp < ts) | ((SyncLog.timestamp == ts) & (SyncLog.id < cid))
            )

    rows = query.limit(limit + 1).all()
    has_more = len(rows) > limit
    items = rows[:limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = f"{last.timestamp.isoformat()}|{last.id}"

    return {
        "items": [
            {
                "id": r.id,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "operation": r.operation,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in items
        ],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }
