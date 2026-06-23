"""磁盘扫描视图路由。

- GET  /scan          —— grid 列表,按 mtime/size/name 排序,复合游标分页
- POST /scan/rescan   —— 手动触发增量扫描(只 stat,秒级),唤醒后台 worker
- GET  /scan/status   —— 队列进度(total/pending/done/failed/running)
- GET  /scan/repos    —— repo 列表,给前端过滤下拉
"""
import logging
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.config import config
from app.models import get_db, FsEntry
from app.schemas.scan import FsEntryResponse, FsEntryCursorResponse, ScanStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["scan"])

_SORT_COLS = {
    "mtime": FsEntry.mtime,
    "size": FsEntry.file_size,
    "name": FsEntry.rel_path,
}


@router.get("", response_model=FsEntryCursorResponse)
def list_scan(
    sort: Literal["mtime", "size", "name"] = Query("mtime"),
    order: Literal["asc", "desc"] = Query("desc"),
    type: Optional[Literal["video", "image"]] = Query(None),
    repo_id: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None, description="复合游标 '{sort_value}|{id}'"),
    limit: int = Query(60, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(FsEntry)
    if type == "video":
        query = query.filter(FsEntry.media_type == "VIDEO")
    elif type == "image":
        query = query.filter(FsEntry.media_type == "IMAGE")
    if repo_id:
        query = query.filter(FsEntry.repo_id == repo_id)

    col = _SORT_COLS[sort]
    desc = order == "desc"

    if cursor:
        try:
            raw, cid_s = cursor.rsplit("|", 1)
            cid = int(cid_s)
            if sort == "mtime":
                cval = float(raw)
            elif sort == "size":
                cval = int(raw)
            else:
                cval = raw
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Invalid cursor format")
        if desc:
            query = query.filter(or_(col < cval, and_(col == cval, FsEntry.id < cid)))
        else:
            query = query.filter(or_(col > cval, and_(col == cval, FsEntry.id > cid)))

    if desc:
        query = query.order_by(col.desc(), FsEntry.id.desc())
    else:
        query = query.order_by(col.asc(), FsEntry.id.asc())

    rows = query.limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        sv = {"mtime": last.mtime, "size": last.file_size, "name": last.rel_path}[sort]
        next_cursor = f"{sv}|{last.id}"

    return FsEntryCursorResponse(
        items=[FsEntryResponse.model_validate(r) for r in rows],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.post("/rescan")
def trigger_rescan():
    """触发增量扫描。阻塞到 stat-walk + sweep 完成(十万秒级),
    metadata/缩略图继续后台异步。已有扫描在跑则 409。"""
    from app.services import scan_service
    result = scan_service.rescan()
    if result is None:
        raise HTTPException(status_code=409, detail="Scan already in progress")
    return result


@router.get("/status", response_model=ScanStatusResponse)
def scan_status(db: Session = Depends(get_db)):
    from app.services import scan_service
    total = db.query(func.count(FsEntry.id)).scalar() or 0
    pending = db.query(func.count(FsEntry.id)).filter(
        (FsEntry.meta_status == "pending") | (FsEntry.thumb_status == "pending")
    ).scalar() or 0
    failed = db.query(func.count(FsEntry.id)).filter(
        (FsEntry.meta_status == "failed") | (FsEntry.thumb_status == "failed")
    ).scalar() or 0
    return ScanStatusResponse(
        total=total,
        pending=pending,
        done=total - pending,
        failed=failed,
        running=scan_service.is_running(),
    )


@router.get("/repos")
def list_repos():
    return [{"repo_id": rid} for rid in config.get_repositories().keys()]
