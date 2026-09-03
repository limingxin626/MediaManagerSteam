"""
SyncLog 变更追踪服务

SQLAlchemy 事件监听器：自动记录 Message, Collection, Media, Tag, Person 的增删改。
"""
import logging
import threading
from datetime import datetime, UTC

from sqlalchemy import event, insert
from sqlalchemy.orm import Session

from app.models import Message, Collection, Media, Tag, Person, SyncLog, Issue

logger = logging.getLogger(__name__)

_TRACKED_MODELS = {
    Message: "MESSAGE",
    Collection: "COLLECTION",
    Media: "MEDIA",
    Tag: "TAG",
    Person: "PERSON",
    Issue: "ISSUE",
}

# thread-local 防止 after_flush 递归
_local = threading.local()
_registration_lock = threading.Lock()
_registered = False


def _after_flush(session: Session, flush_context) -> None:
    """flush 后收集变更，bulk insert 到 sync_log。"""
    if getattr(_local, "in_sync_flush", False):
        return
    _local.in_sync_flush = True
    try:
        now = datetime.now(UTC).replace(tzinfo=None)
        rows = []

        for obj in session.new:
            entity_type = _TRACKED_MODELS.get(type(obj))
            if entity_type:
                rows.append({
                    "entity_type": entity_type,
                    "entity_id": obj.id,
                    "operation": "UPSERT",
                    "timestamp": now,
                })

        for obj in session.dirty:
            entity_type = _TRACKED_MODELS.get(type(obj))
            if entity_type:
                rows.append({
                    "entity_type": entity_type,
                    "entity_id": obj.id,
                    "operation": "UPSERT",
                    "timestamp": now,
                })

        for obj in session.deleted:
            entity_type = _TRACKED_MODELS.get(type(obj))
            if entity_type:
                rows.append({
                    "entity_type": entity_type,
                    "entity_id": obj.id,
                    "operation": "DELETE",
                    "timestamp": now,
                })

        if rows:
            session.execute(insert(SyncLog), rows)
    finally:
        _local.in_sync_flush = False


def _bump_updated_at(target, value, initiator) -> None:
    """关联集合（tags）发生增删时，把宿主对象的 updated_at 推到现在，
    使其进入 session.dirty，被 after_flush 自动写为 UPSERT 日志。
    """
    try:
        target.updated_at = datetime.now(UTC).replace(tzinfo=None)
    except Exception:
        pass


def register_sync_listeners() -> None:
    """注册 SQLAlchemy 事件监听器，应在应用启动时调用一次。"""
    global _registered
    with _registration_lock:
        if _registered:
            return
        event.listen(Session, "after_flush", _after_flush)
        event.listen(Message.tags, "append", _bump_updated_at)
        event.listen(Message.tags, "remove", _bump_updated_at)
        event.listen(Media.tags, "append", _bump_updated_at)
        event.listen(Media.tags, "remove", _bump_updated_at)
        event.listen(Media.people, "append", _bump_updated_at)
        event.listen(Media.people, "remove", _bump_updated_at)
        _registered = True
        logger.info("SyncLog 事件监听器已注册")
