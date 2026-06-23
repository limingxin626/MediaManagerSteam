"""核心映射:Telegram message → backend Message。

负责:
1. 拉取 'me' chat 自 last_message_id 之后的新消息
2. 跳过 service msg / sticker / poll / 无内容消息
3. album(grouped_id)合并为一个 Message
4. 处理大文件缩略图 + RemoteMediaReference
5. 调用 create_message_with_files 落库

入口:`run_cycle(db, client) -> CycleStats`
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from telethon.errors import FloodWaitError
from telethon.tl.types import (
    DocumentAttributeSticker,
    Message,
    MessageMediaContact,
    MessageMediaDice,
    MessageMediaDocument,
    MessageMediaGeo,
    MessageMediaPhoto,
    MessageMediaPoll,
)

from app.models import RemoteMediaReference, Tag
from app.services.message_service import create_message_with_files

from . import download, state

log = logging.getLogger(__name__)

TELEGRAM_TAG_NAME = "#telegram"


# ── Cycle 统计 ────────────────────────────────────────────────────────────


@dataclass
class CycleStats:
    imported: int = 0
    errors: int = 0
    skipped: int = 0
    unsupported: int = 0
    remote_referenced: int = 0

    def summary(self) -> str:
        return (
            f"imported={self.imported} errors={self.errors} "
            f"unsupported={self.unsupported} skipped={self.skipped} "
            f"remote_ref={self.remote_referenced}"
        )


# ── Tag 缓存 ──────────────────────────────────────────────────────────────


_telegram_tag_id: Optional[int] = None


def _get_telegram_tag_id(db: Session) -> int:
    """get_or_create '#telegram' tag,缓存 id。"""
    global _telegram_tag_id
    if _telegram_tag_id is not None:
        return _telegram_tag_id
    tag = db.query(Tag).filter(Tag.name == TELEGRAM_TAG_NAME).one_or_none()
    if tag is None:
        tag = Tag(name=TELEGRAM_TAG_NAME)
        db.add(tag)
        db.commit()
        db.refresh(tag)
    _telegram_tag_id = tag.id
    return tag.id


# ── 主入口 ────────────────────────────────────────────────────────────────


async def run_cycle(db: Session, client) -> CycleStats:
    """执行一轮同步。返回值是统计,异常应在调用方捕获。"""
    stats = CycleStats()
    row = state.get(db)

    # FloodWait 退避期跳过本轮
    if state.is_in_flood_wait(row):
        log.info(
            "skipping cycle: in flood wait until %s",
            row.last_flood_wait_until,
        )
        return stats

    min_id = row.last_message_id or 0
    log.debug("fetching messages with min_id=%s", min_id)

    # Telethon 在 min_id 模式下返回 ASC 顺序
    raw_messages: list[Message] = await client.get_messages(
        "me", min_id=min_id, limit=100
    )
    log.info("got %d new messages from 'me'", len(raw_messages))

    if not raw_messages:
        state.record_success(db, message_id=min_id, count=0)
        return stats

    # 1. 按 grouped_id 分桶
    albums: dict[int, list[Message]] = defaultdict(list)
    standalone: list[Message] = []
    for msg in raw_messages:
        if not _is_candidate(msg):
            stats.skipped += 1
            continue
        if msg.grouped_id:
            albums[msg.grouped_id].append(msg)
        else:
            standalone.append(msg)

    # 2. 处理 albums(整组一个事务)
    for gid in sorted(albums.keys()):
        group = sorted(albums[gid], key=lambda m: m.id)
        if not _import_album(db, group, stats):
            # 失败:不前进游标,等下轮重试(整组都会重新拉到)
            break

    # 3. 处理 standalone
    for msg in standalone:  # 已是 ASC 顺序
        try:
            _import_standalone(db, msg, stats)
        except FloodWaitError as e:
            log.warning("FloodWait %ss during standalone import", e.seconds)
            state.record_flood_wait(db, e.seconds)
            break
        except Exception as e:  # noqa: BLE001
            db.rollback()
            stats.errors += 1
            state.record_error(db, f"{type(e).__name__}: {e}")
            log.exception("standalone msg %s failed", msg.id)

    state.record_success(db, message_id=row.last_message_id, count=stats.imported)
    return stats


# ── 单条 / 单组 import ────────────────────────────────────────────────────


def _import_album(db: Session, group: list[Message], stats: CycleStats) -> bool:
    """album 整组一个 Message。失败 return False 让 caller 不前进游标。"""
    caption = group[0].message or group[0].text or None
    files: list[str] = []
    remote_refs: list[tuple[Message, download.DownloadResult]] = []

    for m in group:
        if not _has_importable_media(m):
            stats.unsupported += 1
            continue
        result = download.to_inbox(m)
        if result is None:
            stats.errors += 1
            log.error("album group download failed for msg %s, aborting group", m.id)
            return False
        files.append(result.media_path)
        if result.is_remote_reference:
            remote_refs.append((m, result))
            stats.remote_referenced += 1

    if not files:
        # 整组都是 unsupported(比如全是 sticker),不创建空 Message
        return True

    try:
        msg_row = create_message_with_files(
            db,
            text=caption,
            actor_id=None,
            files=files,
            tag_ids=[_get_telegram_tag_id(db)],
            created_at=group[0].date,
            commit=True,
        )
        _create_remote_refs(db, remote_refs, msg_row)
        stats.imported += 1
        state.advance(db, max(m.id for m in group))
        return True
    except Exception as e:  # noqa: BLE001
        db.rollback()
        stats.errors += 1
        state.record_error(db, f"album {group[0].grouped_id}: {type(e).__name__}: {e}")
        log.exception("album import failed")
        return False


def _import_standalone(db: Session, msg: Message, stats: CycleStats) -> None:
    """处理单条(非 album)消息。"""
    remote_refs: list[tuple[Message, download.DownloadResult]] = []

    if msg.media:
        if not _has_importable_media(msg):
            stats.unsupported += 1
            return
        result = download.to_inbox(msg)
        if result is None:
            stats.unsupported += 1
            return
        files = [result.media_path]
        if result.is_remote_reference:
            remote_refs.append((msg, result))
            stats.remote_referenced += 1
    else:
        # 纯文本
        files = []

    msg_row = create_message_with_files(
        db,
        text=msg.message or msg.text or None,
        actor_id=None,
        files=files,
        tag_ids=[_get_telegram_tag_id(db)],
        created_at=msg.date,
        commit=True,
    )
    _create_remote_refs(db, remote_refs, msg_row)
    stats.imported += 1
    state.advance(db, msg.id)


# ── RemoteMediaReference 创建 ─────────────────────────────────────────────


def _create_remote_refs(
    db: Session,
    remote_refs: list[tuple[Message, download.DownloadResult]],
    msg_row,
) -> None:
    """commit 之后调:为每个大文件建 RemoteMediaReference 行。

    顺序对齐:`remote_refs[i]` 对应 `msg_row.media` 按 position 升序后的第 i 个。
    """
    if not remote_refs:
        return
    media_in_order = sorted(msg_row.media, key=lambda m: m.position)
    if len(media_in_order) != len(remote_refs):
        log.warning(
            "remote_refs (%d) vs media (%d) count mismatch, skipping ref creation",
            len(remote_refs),
            len(media_in_order),
        )
        return
    for (tg_msg, dl_result), media_row in zip(remote_refs, media_in_order):
        ref = RemoteMediaReference(
            media_id=media_row.id,
            source_type="telegram",
            source_url=_tg_permalink(tg_msg),
            source_msg_id=tg_msg.id,
            source_chat_id=_get_chat_id(tg_msg),
            original_filename=dl_result.original_filename,
            original_size=dl_result.original_size,
            original_mime=dl_result.original_mime,
        )
        db.add(ref)
    db.commit()


def _tg_permalink(msg: Message) -> str:
    """Saved Messages 的 permalink(Saved Messages = 跟自己的对话,chat_id = user_id)。"""
    chat_id = _get_chat_id(msg)
    if chat_id:
        return f"https://t.me/c/{chat_id}/{msg.id}"
    # fallback: tg:// 协议
    return f"tg://msg?id={msg.id}"


def _get_chat_id(msg: Message) -> Optional[int]:
    """从 msg.peer_id 提取 chat_id(user_id for Saved Messages)。"""
    peer = getattr(msg, "peer_id", None)
    if peer is None:
        return None
    user_id = getattr(peer, "user_id", None)
    if user_id:
        return user_id
    channel_id = getattr(peer, "channel_id", None)
    if channel_id:
        # TG permalink 把 channel_id 转成 -100xxx 形式;但我们只服务于 Saved Messages
        return None
    return None


# ── Skip / candidate 判断 ──────────────────────────────────────────────────


def _is_candidate(msg: Message) -> bool:
    """粗筛:这条消息要不要考虑?不消耗 media 字段。"""
    # Service message: joined/left/pinned 等
    if getattr(msg, "action", None) is not None:
        return False
    # 完全空(无文本无 media)
    if msg.media is None and not (msg.message or msg.text):
        return False
    return True


def _has_importable_media(msg: Message) -> bool:
    """精筛:media 是否是 photo/document 这种 process_file 能吃的?"""
    if msg.media is None:
        return False
    # 明确不支持的类型
    if isinstance(
        msg.media,
        (
            MessageMediaPoll,
            MessageMediaContact,
            MessageMediaGeo,
            MessageMediaDice,
        ),
    ):
        return False
    # Photo / Document 接受;但要确保 photo / document 非空(expired)
    if isinstance(msg.media, MessageMediaPhoto):
        return msg.media.photo is not None
    if isinstance(msg.media, MessageMediaDocument):
        if msg.media.document is None:
            return False
        # 排除 sticker(在 telethon 里 sticker 是 MessageMediaDocument + DocumentAttributeSticker)
        if any(
            isinstance(a, DocumentAttributeSticker)
            for a in (msg.media.document.attributes or [])
        ):
            return False
        return True
    return False