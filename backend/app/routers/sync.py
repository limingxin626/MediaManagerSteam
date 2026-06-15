"""
同步路由

- GET  /sync/changes      增量拉取变更
- POST /api/sync/apply    推送客户端变更
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import (
    get_db, SyncLog, Message, Actor, Media, Tag, MessageMedia, message_tag
)
from app.schemas.sync import (
    SyncChangesResponse, SyncChangeItem,
    SyncApplyRequest, SyncApplyResponse,
)
from app.config import config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sync"])

SYNC_LOG_RETENTION_DAYS = 365


# ---------------------------------------------------------------------------
# 实体快照构建
# ---------------------------------------------------------------------------

def _message_snapshot(db: Session, msg: Message) -> Dict[str, Any]:
    relations = (
        db.query(MessageMedia)
        .filter(MessageMedia.message_id == msg.id)
        .order_by(MessageMedia.position)
        .all()
    )
    media_items = []
    for r in relations:
        if r.media:
            m = r.media
            media_items.append({
                "id": m.id,
                "repo_id": m.repo_id,
                "file_path": m.file_path,
                "local_file_path": config.resolve_to_absolute(m.repo_id, m.file_path) or "",
                "local_thumb_path": config.get_thumbnail_path(m.id),
                "file_url": config.url_for(m.repo_id, m.file_path),
                "thumb_url": config.get_thumbnail_url(m.id),
                "file_hash": m.file_hash or "",
                "file_size": m.file_size,
                "mime_type": m.mime_type,
                "width": m.width,
                "height": m.height,
                "duration_ms": m.duration_ms,
                "rating": m.rating,
                "starred": bool(m.starred),
                "position": r.position,
                "video_media_id": m.video_media_id,
                "frame_ms": m.frame_ms,
                "start_ms": m.start_ms,
                "end_ms": m.end_ms,
            })
    tags = [{"id": t.id, "name": t.name, "category": t.category} for t in msg.tags]
    return {
        "id": msg.id,
        "text": msg.text,
        "actor_id": msg.actor_id,
        "actor_name": msg.actor.name if msg.actor else None,
        "starred": bool(msg.starred),
        "created_at": msg.created_at.isoformat(),
        "updated_at": msg.updated_at.isoformat(),
        "media_items": media_items,
        "tags": tags,
    }


def _actor_snapshot(actor: Actor) -> Dict[str, Any]:
    return {
        "id": actor.id,
        "name": actor.name,
        "description": actor.description,
        "avatar": config.get_actor_avatar_url(actor.id) if actor.avatar_path else None,
        "created_at": actor.created_at.isoformat(),
        "updated_at": actor.updated_at.isoformat(),
    }


def _media_snapshot(media: Media) -> Dict[str, Any]:
    # 6 字段标准见 CLAUDE.md「Pydantic schema validators」段:
    #   - file_path     相对 repo 根
    #   - local_*_path  本机绝对路径(Vue/Electron 直读)
    #   - *_url         相对 URL(Android 拼 baseUrl)
    return {
        "id": media.id,
        "repo_id": media.repo_id,
        "file_path": media.file_path,
        "local_file_path": config.resolve_to_absolute(media.repo_id, media.file_path) or "",
        "local_thumb_path": config.get_thumbnail_path(media.id),
        "file_url": config.url_for(media.repo_id, media.file_path),
        "thumb_url": config.get_thumbnail_url(media.id),
        "file_hash": media.file_hash or "",
        "file_size": media.file_size,
        "mime_type": media.mime_type,
        "width": media.width,
        "height": media.height,
        "duration_ms": media.duration_ms,
        "rating": media.rating,
        "starred": bool(media.starred),
        "video_media_id": media.video_media_id,
        "frame_ms": media.frame_ms,
        "start_ms": media.start_ms,
        "end_ms": media.end_ms,
        "created_at": media.created_at.isoformat(),
        "updated_at": media.updated_at.isoformat(),
    }


def _tag_snapshot(tag: Tag) -> Dict[str, Any]:
    return {
        "id": tag.id,
        "name": tag.name,
        "category": tag.category,
    }


def _fetch_snapshot(db: Session, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
    if entity_type == "MESSAGE":
        obj = db.query(Message).filter(Message.id == entity_id).first()
        return _message_snapshot(db, obj) if obj else None
    elif entity_type == "ACTOR":
        obj = db.query(Actor).filter(Actor.id == entity_id).first()
        return _actor_snapshot(obj) if obj else None
    elif entity_type == "MEDIA":
        obj = db.query(Media).filter(Media.id == entity_id).first()
        return _media_snapshot(obj) if obj else None
    elif entity_type == "TAG":
        obj = db.query(Tag).filter(Tag.id == entity_id).first()
        return _tag_snapshot(obj) if obj else None
    return None


# ---------------------------------------------------------------------------
# GET /sync/changes
# ---------------------------------------------------------------------------

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
    server_time = datetime.utcnow().isoformat()

    if not since:
        raise HTTPException(status_code=410, detail="since 参数缺失，请执行全量同步")

    try:
        since_dt = datetime.fromisoformat(since)
    except ValueError:
        raise HTTPException(status_code=400, detail="since 格式无效，应为 ISO timestamp")

    # 超过保留期
    cutoff = datetime.utcnow() - timedelta(days=SYNC_LOG_RETENTION_DAYS)
    if since_dt < cutoff:
        raise HTTPException(status_code=410, detail="since 超过保留期（1年），请执行全量同步")

    # 复合游标过滤：(timestamp > since_dt) OR (timestamp = since_dt AND id > since_id)
    rows = (
        db.query(SyncLog)
        .filter(
            (SyncLog.timestamp > since_dt) |
            ((SyncLog.timestamp == since_dt) & (SyncLog.id > since_id))
        )
        .order_by(SyncLog.timestamp.asc(), SyncLog.id.asc())
        .limit(limit + 1)
        .all()
    )
    has_more = len(rows) > limit
    rows = rows[:limit]

    # 去重：同一 (entity_type, entity_id) 只保留最新条目（rows 已按时间升序，取 last）
    # 但若本页内出现过 DELETE，则强制保留 DELETE —— 否则后续 UPSERT 会让客户端误以为实体仍存在。
    seen: dict[tuple, SyncLog] = {}
    deleted_keys: set[tuple] = set()
    for row in rows:
        key = (row.entity_type, row.entity_id)
        if row.operation == "DELETE":
            deleted_keys.add(key)
            seen[key] = row
        elif key not in deleted_keys:
            seen[key] = row
    deduped = sorted(seen.values(), key=lambda r: (r.timestamp, r.id))

    # 构建响应
    changes = []
    for log in deduped:
        if log.operation == "DELETE":
            data = None
        else:
            data = _fetch_snapshot(db, log.entity_type, log.entity_id)
            if data is None:
                # 实体已被删除，改为 DELETE
                log.operation = "DELETE"

        changes.append(SyncChangeItem(
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            operation=log.operation,
            timestamp=log.timestamp.isoformat(),
            data=data,
        ))

    # 下一页游标：使用 (timestamp, id) 复合值
    if has_more and deduped:
        last = deduped[-1]
        next_cursor = last.timestamp.isoformat()
        next_cursor_id = last.id
    else:
        next_cursor = None
        next_cursor_id = None

    return SyncChangesResponse(
        changes=changes,
        next_cursor=next_cursor,
        next_cursor_id=next_cursor_id,
        has_more=has_more,
        server_time=server_time,
    )


# ---------------------------------------------------------------------------
# POST /api/sync/apply
# ---------------------------------------------------------------------------

@router.post("/api/sync/apply", response_model=SyncApplyResponse)
def apply_sync_changes(
    body: SyncApplyRequest,
    db: Session = Depends(get_db),
):
    """接收 Android 客户端推送的变更，按序应用。Last-write-wins by updated_at。

    整个批次在单一事务中执行：全部成功才 commit，任意失败则全量 rollback。
    """
    applied = 0
    failed = 0
    errors = []

    try:
        for item in body.changes:
            entity_type = item.entityType.upper()
            operation = item.operation.upper()
            entity_id = item.entityId
            payload = item.payload or {}

            if operation == "DELETE":
                _apply_delete(db, entity_type, entity_id)
            elif operation == "UPSERT":
                _apply_upsert(db, entity_type, entity_id, payload)
            else:
                logger.warning("未知 operation: %s", operation)
                errors.append(f"未知 operation: {operation}")
                failed += 1
                continue

            applied += 1

        db.commit()
    except Exception as e:
        logger.error("apply_sync_changes 批量提交失败，全量 rollback: %s", e)
        db.rollback()
        # 整批失败：已计数的均视为失败
        failed += applied
        applied = 0

    return SyncApplyResponse(applied=applied, failed=failed)


def _apply_delete(db: Session, entity_type: str, entity_id: int) -> None:
    model_map = {"MESSAGE": Message, "ACTOR": Actor, "MEDIA": Media, "TAG": Tag}
    model = model_map.get(entity_type)
    if not model:
        return
    obj = db.query(model).filter(model.id == entity_id).first()
    if obj:
        if entity_type == "MESSAGE":
            db.query(MessageMedia).filter(MessageMedia.message_id == entity_id).delete()
            db.execute(message_tag.delete().where(message_tag.c.message_id == entity_id))
        db.delete(obj)


def _apply_upsert(db: Session, entity_type: str, entity_id: int, payload: dict) -> None:
    if entity_type == "MESSAGE":
        _upsert_message(db, entity_id, payload)
    elif entity_type == "ACTOR":
        _upsert_actor(db, entity_id, payload)
    elif entity_type == "MEDIA":
        _upsert_media(db, entity_id, payload)
    elif entity_type == "TAG":
        _upsert_tag(db, entity_id, payload)


def _parse_dt(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def _upsert_message(db: Session, entity_id: int, payload: dict) -> None:
    existing = db.query(Message).filter(Message.id == entity_id).first()
    incoming_updated = _parse_dt(payload.get("updatedAt") or payload.get("updated_at"))

    if existing:
        if "text" in payload:
            existing.text = payload["text"]
        if "actorId" in payload or "actor_id" in payload:
            existing.actor_id = payload.get("actorId") or payload.get("actor_id")
        if "starred" in payload:
            existing.starred = 1 if payload["starred"] else 0
        existing.updated_at = incoming_updated or datetime.utcnow()
    else:
        created_at = _parse_dt(payload.get("createdAt") or payload.get("created_at")) or datetime.utcnow()
        msg = Message(
            id=entity_id,
            text=payload.get("text"),
            actor_id=payload.get("actorId") or payload.get("actor_id"),
            starred=1 if payload.get("starred") else 0,
            created_at=created_at,
            updated_at=incoming_updated or datetime.utcnow(),
        )
        db.add(msg)
        db.flush()


def _upsert_actor(db: Session, entity_id: int, payload: dict) -> None:
    existing = db.query(Actor).filter(Actor.id == entity_id).first()
    incoming_updated = _parse_dt(payload.get("updatedAt") or payload.get("updated_at"))

    if existing:
        if "name" in payload:
            existing.name = payload["name"]
        if "description" in payload:
            existing.description = payload["description"]
        existing.updated_at = incoming_updated or datetime.utcnow()
    else:
        created_at = _parse_dt(payload.get("createdAt") or payload.get("created_at")) or datetime.utcnow()
        actor = Actor(
            id=entity_id,
            name=payload.get("name", ""),
            description=payload.get("description"),
            created_at=created_at,
            updated_at=incoming_updated or datetime.utcnow(),
        )
        db.add(actor)


def _upsert_media(db: Session, entity_id: int, payload: dict) -> None:
    existing = db.query(Media).filter(Media.id == entity_id).first()
    incoming_updated = _parse_dt(payload.get("updatedAt") or payload.get("updated_at"))

    if existing:
        for src, dst in [("rating", "rating"), ("starred", "starred")]:
            if src in payload:
                val = payload[src]
                setattr(existing, dst, (1 if val else 0) if dst == "starred" else val)
        existing.updated_at = incoming_updated or datetime.utcnow()
    else:
        # Media 通常由后端通过文件上传创建；Android 一般不会创建新 Media
        logger.debug("MEDIA UPSERT: id=%s 不存在，跳过", entity_id)


def _upsert_tag(db: Session, entity_id: int, payload: dict) -> None:
    existing = db.query(Tag).filter(Tag.id == entity_id).first()
    if existing:
        if "name" in payload:
            existing.name = payload["name"]
        if "category" in payload:
            existing.category = payload["category"]
    else:
        tag = Tag(
            id=entity_id,
            name=payload.get("name", ""),
            category=payload.get("category"),
        )
        db.add(tag)
