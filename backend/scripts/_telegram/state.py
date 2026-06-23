"""TelegramSyncState 单行表的读写。

约定:id=1 是唯一行。新进程第一次访问前调用 `seed(db)` 一次性 INSERT OR IGNORE。
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import TelegramSyncState

log = logging.getLogger(__name__)


def seed(db: Session) -> None:
    """确保 id=1 行存在。INSERT OR IGNORE 语义,已有则无操作。"""
    db.execute(
        text("INSERT OR IGNORE INTO telegram_sync_state (id) VALUES (1)")
    )
    db.commit()


def get(db: Session) -> TelegramSyncState:
    """读单行;若不存在(种子失败)则返回新建的 detached 行,等下次 save() 落库。"""
    seed(db)
    row = db.query(TelegramSyncState).filter(TelegramSyncState.id == 1).one_or_none()
    if row is None:
        # 极端情况:并发 INSERT 失败后看到真空,补一行
        row = TelegramSyncState(id=1)
        db.add(row)
        db.flush()
    return row


def advance(db: Session, message_id: int) -> None:
    """成功 import 后,把 last_message_id 推到 message_id(取 max)。"""
    row = get(db)
    if message_id > row.last_message_id:
        row.last_message_id = message_id


def record_success(db: Session, message_id: int, count: int = 1) -> None:
    """成功路径:推进游标 + 增加累计计数 + 清空 last_error。"""
    row = get(db)
    if message_id > row.last_message_id:
        row.last_message_id = message_id
    row.total_imported = (row.total_imported or 0) + count
    row.last_sync_at = datetime.now()
    row.last_error = None
    db.commit()


def record_error(db: Session, err: str) -> None:
    """失败路径:只记 last_error,不动 last_message_id(下轮重试)。"""
    row = get(db)
    row.last_sync_at = datetime.now()
    row.last_error = err
    db.commit()


def record_flood_wait(db: Session, seconds: int) -> None:
    """Telegram 返回 FloodWaitError:记退避截止时间 + last_error。

    不动 last_message_id —— 下轮会拉到同一批消息,TG 会再返回 FloodWait,
    此时我们已经 sleep 过、不会触发新限流。
    """
    row = get(db)
    row.last_error = f"FloodWait:{seconds}s"
    row.last_flood_wait_until = datetime.now() + timedelta(seconds=seconds + 5)
    db.commit()


def is_in_flood_wait(row: TelegramSyncState) -> bool:
    """是否仍在 FloodWait 退避期内。"""
    if row.last_flood_wait_until is None:
        return False
    return datetime.now() < row.last_flood_wait_until