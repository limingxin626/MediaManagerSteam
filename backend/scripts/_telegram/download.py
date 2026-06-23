"""Telegram media 下载 + 大文件只下封面策略。

入口:`to_inbox(msg) -> DownloadResult | None`
- 普通文件:下载到 <TELEGRAM_INBOX_DIR>/<msg_id>.<ext>
- 大文件(>= TELEGRAM_LARGE_FILE_THRESHOLD):只下 document.thumb,
  is_remote_reference=True,让 caller 建 RemoteMediaReference 行。
"""
from __future__ import annotations

import logging
import mimetypes
import os
from dataclasses import dataclass
from typing import Optional

from telethon.tl.types import (
    DocumentAttributeFilename,
    MessageMediaDocument,
    MessageMediaPhoto,
)

from app.config import config

log = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """下载结果。

    - `media_path`: 本地文件路径(原图 / 原文件 / 缩略图 都有可能)
    - `is_remote_reference`: True 表示原文件未下载,`media_path` 是缩略图
    - 其他字段是原文件的元数据(供 RemoteMediaReference 记录)
    """

    media_path: str
    is_remote_reference: bool
    original_size: Optional[int] = None
    original_filename: Optional[str] = None
    original_mime: Optional[str] = None


# ── 公开入口 ──────────────────────────────────────────────────────────────


def to_inbox(msg) -> Optional[DownloadResult]:
    """下载 msg 媒体到 inbox 目录。失败返回 None。"""
    if _is_large(msg):
        return _download_thumb_only(msg)
    return _download_full(msg)


# ── 大文件检测 ────────────────────────────────────────────────────────────


def _is_large(msg) -> bool:
    """仅对 document 类型判断大小;photo 极少 >50MB,始终下载原图。"""
    if not isinstance(msg.media, MessageMediaDocument):
        return False
    size = getattr(msg.media.document, "size", 0) or 0
    return size >= config.TELEGRAM_LARGE_FILE_THRESHOLD


# ── 普通下载 ──────────────────────────────────────────────────────────────


def _download_full(msg) -> Optional[DownloadResult]:
    """下载原文件到 <inbox>/<msg_id>.<ext>(同名文件已存在则复用)。"""
    ext = _guess_ext(msg)
    dest = os.path.join(config.get_telegram_inbox_dir(), f"{msg.id}{ext}")
    if os.path.exists(dest):
        return DownloadResult(
            media_path=dest,
            is_remote_reference=False,
            original_size=_get_doc_size(msg),
            original_filename=_get_filename(msg),
            original_mime=_get_mime(msg),
        )
    try:
        path = msg.client.download_media(msg, file=dest)
        if not path:
            return None
        return DownloadResult(
            media_path=path,
            is_remote_reference=False,
            original_size=_get_doc_size(msg),
            original_filename=_get_filename(msg),
            original_mime=_get_mime(msg),
        )
    except Exception as e:  # noqa: BLE001
        log.warning("download_media failed for msg %s: %s", msg.id, e)
        return None


# ── 缩略图下载(大文件)─────────────────────────────────────────────────────


def _download_thumb_only(msg) -> Optional[DownloadResult]:
    """只下 document.thumb,不下载原文件。"""
    doc = msg.media.document if isinstance(msg.media, MessageMediaDocument) else None
    if not doc or not getattr(doc, "thumb", None):
        log.warning(
            "large msg %s (%s bytes): no thumb available, skipping",
            msg.id,
            getattr(doc, "size", 0) if doc else "?",
        )
        return None
    ext = _guess_thumb_ext(doc.thumb)
    dest = os.path.join(config.get_telegram_inbox_dir(), f"{msg.id}_thumb{ext}")
    if os.path.exists(dest):
        return DownloadResult(
            media_path=dest,
            is_remote_reference=True,
            original_size=getattr(doc, "size", None),
            original_filename=_get_filename(msg),
            original_mime=getattr(doc, "mime_type", None),
        )
    try:
        # thumb=True 让 Telethon 走 photo 路径,不会触发原文件下载
        path = msg.client.download_media(msg, file=dest, thumb=True)
        if not path:
            return None
        return DownloadResult(
            media_path=path,
            is_remote_reference=True,
            original_size=getattr(doc, "size", None),
            original_filename=_get_filename(msg),
            original_mime=getattr(doc, "mime_type", None),
        )
    except Exception as e:  # noqa: BLE001
        log.warning("download thumb failed for msg %s: %s", msg.id, e)
        return None


# ── 扩展名 / 元数据辅助 ────────────────────────────────────────────────────


def _guess_ext(msg) -> str:
    """从 msg.media 推断扩展名(含点)。失败回退到 .bin。"""
    if isinstance(msg.media, MessageMediaPhoto):
        return ".jpg"
    doc = msg.media.document if isinstance(msg.media, MessageMediaDocument) else None
    if doc and doc.mime_type:
        ext = mimetypes.guess_extension(doc.mime_type)
        if ext:
            return ext
    if doc and doc.attributes:
        for attr in doc.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                name_ext = os.path.splitext(attr.file_name)[1]
                if name_ext:
                    return name_ext
    return ".bin"


def _guess_thumb_ext(thumb) -> str:
    """缩略图通常是 jpg/png。Telethon PhotoSize 没有 mime 字段,默认 jpg。"""
    return ".jpg"


def _get_doc_size(msg) -> Optional[int]:
    if isinstance(msg.media, MessageMediaDocument) and msg.media.document:
        return getattr(msg.media.document, "size", None)
    return None


def _get_filename(msg) -> Optional[str]:
    if isinstance(msg.media, MessageMediaDocument) and msg.media.document:
        for attr in msg.media.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                return attr.file_name
    return None


def _get_mime(msg) -> Optional[str]:
    if isinstance(msg.media, MessageMediaDocument) and msg.media.document:
        return getattr(msg.media.document, "mime_type", None)
    return None