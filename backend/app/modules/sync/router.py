"""HTTP boundary for backend and Android synchronization."""
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import get_db
from app.modules.sync.service import apply_batch, get_changes
from app.modules.sync.schemas import SyncApplyRequest, SyncApplyResponse, SyncChangeItem, SyncChangesResponse
from app.config import config

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sync"])
SYNC_LOG_RETENTION_DAYS = 365


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@router.get("/sync/changes", response_model=SyncChangesResponse)
def get_sync_changes(
    since: Optional[str] = Query(None, description="ISO timestamp 游标，为空则返回 410 要求全量同步"),
    since_id: int = Query(0, description="复合游标：上次最后一条 SyncLog.id，与 since 配合使用"),
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """增量拉取变更日志。since 为空或超过保留期返回 410，客户端应回退到全量同步。

    游标格式升级为 (timestamp, id) 复合游标，避免同一 timestamp 多行时跳页：
    过滤条件等价于 (timestamp > since_dt) OR (timestamp = since_dt AND id > since_id)。
    """
    server_time = _utcnow().isoformat()
    if not since:
        raise HTTPException(status_code=410, detail="since 参数缺失，请执行全量同步")
    try:
        since_dt = datetime.fromisoformat(since)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="since 格式无效，应为 ISO timestamp") from exc
    if since_dt < _utcnow() - timedelta(days=SYNC_LOG_RETENTION_DAYS):
        raise HTTPException(status_code=410, detail="since 超过保留期（1年），请执行全量同步")

    return get_changes(db, since_dt, since_id, limit, server_time)


@router.post("/api/sync/apply", response_model=SyncApplyResponse)
def apply_sync_changes(body: SyncApplyRequest, db: Session = Depends(get_db)):
    """接收 Android 客户端推送的变更，按序应用。Last-write-wins by updated_at。

    整个批次在单一事务中执行：全部成功才 commit，任意失败则全量 rollback。
    """
    try:
        applied, failed = apply_batch(db, body.changes)
    except Exception as exc:
        logger.error("apply_sync_changes 批量提交失败，全量 rollback: %s", exc)
        failed = len(body.changes)
        applied = 0
    return SyncApplyResponse(applied=applied, failed=failed)
