"""
SyncLog 变更追踪服务

- SQLAlchemy 事件监听器：自动记录 Message, Actor, Media, Tag 的增删改
- 进程内事件总线：SSE 端点订阅，数据变更时广播通知
"""
import asyncio
import logging
import threading
from datetime import datetime

from sqlalchemy import event, insert
from sqlalchemy.orm import Session

from app.models import Message, Actor, Media, Tag, SyncLog

logger = logging.getLogger(__name__)

# 需要追踪的模型 → entity_type 名称
_TRACKED_MODELS = {
    Message: "MESSAGE",
    Actor: "ACTOR",
    Media: "MEDIA",
    Tag: "TAG",
}

# 用 thread-local 防止 after_flush 递归
_local = threading.local()


# ---------------------------------------------------------------------------
# 进程内 SSE 事件总线
# ---------------------------------------------------------------------------

_subscribers: list[asyncio.Queue] = []
_subscribers_lock = threading.Lock()

_SSE_QUEUE_MAXSIZE = 100


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=_SSE_QUEUE_MAXSIZE)
    with _subscribers_lock:
        _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    with _subscribers_lock:
        try:
            _subscribers.remove(q)
        except ValueError:
            pass


def _broadcast(entity_type: str, entity_id: int, operation: str, timestamp: str) -> None:
    event_data = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "operation": operation,
        "timestamp": timestamp,
    }
    stale: list[asyncio.Queue] = []
    with _subscribers_lock:
        snapshot = list(_subscribers)
    for q in snapshot:
        try:
            q.put_nowait(event_data)
        except asyncio.QueueFull:
            # 队列满说明客户端已失联，标记为需清除
            stale.append(q)
        except Exception:
            stale.append(q)
    if stale:
        with _subscribers_lock:
            for q in stale:
                try:
                    _subscribers.remove(q)
                except ValueError:
                    pass


# ---------------------------------------------------------------------------
# SQLAlchemy 事件监听器
# ---------------------------------------------------------------------------

def _after_flush(session: Session, flush_context) -> None:
    """在 flush 后收集变更，用 bulk insert 写入 sync_log 避免递归。"""
    # 防递归：如果正在写 sync_log，直接返回
    if getattr(_local, "in_sync_flush", False):
        return
    _local.in_sync_flush = True
    try:
        now = datetime.utcnow()
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


def _after_commit(session: Session) -> None:
    """commit 完成后广播变更通知给 SSE 客户端。"""
    _broadcast("*", 0, "REFRESH", datetime.utcnow().isoformat())


def register_sync_listeners() -> None:
    """注册 SQLAlchemy 事件监听器，应在应用启动时调用一次。"""
    event.listen(Session, "after_flush", _after_flush)
    event.listen(Session, "after_commit", _after_commit)
    logger.info("SyncLog 事件监听器已注册")
