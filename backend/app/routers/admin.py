from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import get_db, Message, Media, Actor, Tag, MessageMedia, SyncLog, message_tag
from app.config import config
import os

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取数据库统计信息：各表记录数、存储统计、最近活动。"""
    # 各表记录数
    table_counts = {
        "message": db.query(func.count(Message.id)).scalar(),
        "media": db.query(func.count(Media.id)).scalar(),
        "actor": db.query(func.count(Actor.id)).scalar(),
        "tag": db.query(func.count(Tag.id)).scalar(),
        "message_media": db.query(func.count(MessageMedia.id)).scalar(),
        "message_tag": db.query(func.count()).select_from(message_tag).scalar(),
        "sync_log": db.query(func.count(SyncLog.id)).scalar(),
    }

    # 媒体存储统计
    storage = db.query(
        func.count(Media.id),
        func.coalesce(func.sum(Media.file_size), 0),
    ).one()
    storage_stats = {
        "total_files": storage[0],
        "total_size": storage[1],
    }

    # 最近 5 条 Message
    recent_messages = (
        db.query(Message)
        .order_by(Message.created_at.desc())
        .limit(5)
        .all()
    )
    recent = [
        {
            "id": m.id,
            "text": (m.text[:100] if m.text else None),
            "actor_id": m.actor_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in recent_messages
    ]

    # 数据库文件大小
    db_path = config.get_db_path()
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    return {
        "table_counts": table_counts,
        "storage": storage_stats,
        "db_size": db_size,
        "recent_messages": recent,
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
