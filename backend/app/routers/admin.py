from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.models import get_db, SyncLog

router = APIRouter(prefix="/admin", tags=["admin"])


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
