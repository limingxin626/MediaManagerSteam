"""Sync snapshots and mutation helpers, independent from HTTP routing."""
import logging
from datetime import datetime, UTC
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.config import config
from app.models import Message, Collection, Media, Tag, Person, MessageMedia, SyncLog, message_tag
from app.modules.sync.schemas import SyncChangeItem, SyncChangesResponse
from app.shared.unit_of_work import commit

logger = logging.getLogger(__name__)


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
        "collection_id": msg.collection_id,
        "collection_name": msg.collection.name if msg.collection else None,
        "starred": bool(msg.starred),
        "created_at": msg.created_at.isoformat(),
        "updated_at": msg.updated_at.isoformat(),
        "media_items": media_items,
        "tags": tags,
    }


def _collection_snapshot(collection: Collection) -> Dict[str, Any]:
    return {
        "id": collection.id,
        "name": collection.name,
        "description": collection.description,
        "cover": config.get_collection_cover_url(collection.id) if collection.cover_path else None,
        "created_at": collection.created_at.isoformat(),
        "updated_at": collection.updated_at.isoformat(),
    }


def _person_snapshot(person: Person) -> Dict[str, Any]:
    return {
        "id": person.id,
        "name": person.name,
        "description": person.description,
        "cover": config.get_person_cover_url(person.id) if person.cover_path else None,
        "created_at": person.created_at.isoformat(),
        "updated_at": person.updated_at.isoformat(),
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
        "people": [{"id": p.id, "name": p.name} for p in media.people],
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
        obj = db.query(Message).filter(
            Message.id == entity_id,
            ~Message.folder_links.any(),
        ).first()
        return _message_snapshot(db, obj) if obj else None
    elif entity_type == "COLLECTION":
        obj = db.query(Collection).filter(Collection.id == entity_id).first()
        return _collection_snapshot(obj) if obj else None
    elif entity_type == "PERSON":
        obj = db.query(Person).filter(Person.id == entity_id).first()
        return _person_snapshot(obj) if obj else None
    elif entity_type == "MEDIA":
        obj = db.query(Media).filter(Media.id == entity_id).first()
        return _media_snapshot(obj) if obj else None
    elif entity_type == "TAG":
        obj = db.query(Tag).filter(Tag.id == entity_id).first()
        return _tag_snapshot(obj) if obj else None
    return None

def _apply_delete(db: Session, entity_type: str, entity_id: int) -> None:
    model_map = {"MESSAGE": Message, "COLLECTION": Collection, "MEDIA": Media, "TAG": Tag, "PERSON": Person}
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
    elif entity_type == "COLLECTION":
        _upsert_collection(db, entity_id, payload)
    elif entity_type == "PERSON":
        _upsert_person(db, entity_id, payload)
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
        if any(k in payload for k in ("collectionId", "collection_id", "actorId", "actor_id")):
            existing.collection_id = (
                payload.get("collectionId") or payload.get("collection_id")
                or payload.get("actorId") or payload.get("actor_id")
            )
        if "starred" in payload:
            existing.starred = 1 if payload["starred"] else 0
        existing.updated_at = incoming_updated or datetime.now(UTC).replace(tzinfo=None)
    else:
        created_at = _parse_dt(payload.get("createdAt") or payload.get("created_at")) or datetime.now(UTC).replace(tzinfo=None)
        msg = Message(
            id=entity_id,
            text=payload.get("text"),
            collection_id=(
                payload.get("collectionId") or payload.get("collection_id")
                or payload.get("actorId") or payload.get("actor_id")
            ),
            starred=1 if payload.get("starred") else 0,
            created_at=created_at,
            updated_at=incoming_updated or datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(msg)
        db.flush()


def _upsert_collection(db: Session, entity_id: int, payload: dict) -> None:
    existing = db.query(Collection).filter(Collection.id == entity_id).first()
    incoming_updated = _parse_dt(payload.get("updatedAt") or payload.get("updated_at"))

    if existing:
        if "name" in payload:
            existing.name = payload["name"]
        if "description" in payload:
            existing.description = payload["description"]
        existing.updated_at = incoming_updated or datetime.now(UTC).replace(tzinfo=None)
    else:
        created_at = _parse_dt(payload.get("createdAt") or payload.get("created_at")) or datetime.now(UTC).replace(tzinfo=None)
        collection = Collection(
            id=entity_id,
            name=payload.get("name", ""),
            description=payload.get("description"),
            created_at=created_at,
            updated_at=incoming_updated or datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(collection)


def _upsert_person(db: Session, entity_id: int, payload: dict) -> None:
    existing = db.query(Person).filter(Person.id == entity_id).first()
    incoming_updated = _parse_dt(payload.get("updatedAt") or payload.get("updated_at"))

    if existing:
        if "name" in payload:
            existing.name = payload["name"]
        if "description" in payload:
            existing.description = payload["description"]
        existing.updated_at = incoming_updated or datetime.now(UTC).replace(tzinfo=None)
    else:
        created_at = _parse_dt(payload.get("createdAt") or payload.get("created_at")) or datetime.now(UTC).replace(tzinfo=None)
        person = Person(
            id=entity_id,
            name=payload.get("name", ""),
            description=payload.get("description"),
            created_at=created_at,
            updated_at=incoming_updated or datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(person)


def _upsert_media(db: Session, entity_id: int, payload: dict) -> None:
    existing = db.query(Media).filter(Media.id == entity_id).first()
    incoming_updated = _parse_dt(payload.get("updatedAt") or payload.get("updated_at"))

    if existing:
        for src, dst in [("rating", "rating"), ("starred", "starred")]:
            if src in payload:
                val = payload[src]
                setattr(existing, dst, (1 if val else 0) if dst == "starred" else val)
        existing.updated_at = incoming_updated or datetime.now(UTC).replace(tzinfo=None)
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


# Stable public names consumed by the HTTP boundary.
fetch_snapshot = _fetch_snapshot
apply_delete = _apply_delete
apply_upsert = _apply_upsert


def apply_batch(db: Session, changes) -> tuple[int, int]:
    """Apply one client batch as a single transaction."""
    applied = 0
    failed = 0
    try:
        for item in changes:
            operation = item.operation.upper()
            if operation == "DELETE":
                _apply_delete(db, item.entityType.upper(), item.entityId)
            elif operation == "UPSERT":
                _apply_upsert(db, item.entityType.upper(), item.entityId, item.payload or {})
            else:
                logger.warning("未知 operation: %s", operation)
                failed += 1
                continue
            applied += 1
        commit(db)
    except Exception:
        db.rollback()
        raise
    return applied, failed


def get_changes(db: Session, since: datetime, since_id: int, limit: int, server_time: str) -> SyncChangesResponse:
    rows = db.query(SyncLog).filter((SyncLog.timestamp > since) | ((SyncLog.timestamp == since) & (SyncLog.id > since_id))).order_by(SyncLog.timestamp, SyncLog.id).limit(limit + 1).all()
    has_more, rows = len(rows) > limit, rows[:limit]
    seen = {}
    deleted = set()
    for row in rows:
        key = (row.entity_type, row.entity_id)
        if row.operation == "DELETE":
            deleted.add(key)
            seen[key] = row
        elif key not in deleted:
            seen[key] = row
    deduped = sorted(seen.values(), key=lambda row: (row.timestamp, row.id))
    changes = []
    for log in deduped:
        data = None if log.operation == "DELETE" else _fetch_snapshot(db, log.entity_type, log.entity_id)
        operation = "DELETE" if log.operation != "DELETE" and data is None else log.operation
        changes.append(SyncChangeItem(entity_type=log.entity_type, entity_id=log.entity_id, operation=operation, timestamp=log.timestamp.isoformat(), data=data))
    last = deduped[-1] if has_more and deduped else None
    return SyncChangesResponse(changes=changes, next_cursor=last.timestamp.isoformat() if last else None, next_cursor_id=last.id if last else None, has_more=has_more, server_time=server_time)
