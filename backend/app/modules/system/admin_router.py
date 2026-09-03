"""HTTP boundary for administration reports."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import get_db
from app.modules.system import service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return service.admin_stats(db)


@router.get("/sync-logs")
def get_sync_logs(cursor: str | None = Query(None, description="分页游标 (ISO datetime)"), limit: int = Query(20, ge=1, le=100), entity_type: str | None = Query(None, description="按实体类型筛选"), db: Session = Depends(get_db)):
    try:
        return service.sync_logs(db, cursor, limit, entity_type)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc
