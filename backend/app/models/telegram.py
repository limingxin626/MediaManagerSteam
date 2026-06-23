"""Telegram "Saved Messages" 同步相关 ORM。

- TelegramSyncState: 单行,sync 游标 + 状态(last_message_id / last_error / flood wait)。
- RemoteMediaReference: 大文件未下载原文件的引用记录,保留以后按需下载的可能。
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models import Base


class TelegramSyncState(Base):
    """Telegram sync 单行配置(id 强制 = 1)。

    `last_message_id` 是单调递增游标:轮询时 `iter_messages('me', min_id=last_message_id)`。
    `last_flood_wait_until`: 若 Telegram 返回 FloodWaitError,在该时间前跳过下一轮。
    """

    __tablename__ = "telegram_sync_state"

    id = Column(Integer, primary_key=True, default=1)  # 单行,singleton
    last_message_id = Column(Integer, nullable=False, default=0)
    last_sync_at = Column(DateTime, nullable=True)
    total_imported = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    last_flood_wait_until = Column(DateTime, nullable=True)


class RemoteMediaReference(Base):
    """指向远端尚未下载的原始文件,`media_id` 是已入库的缩略图/封面 Media 行。

    业务语义:这行存在 → 对应的 Media 是一张缩略图,原文件仍在远端。
    前端可据此显示 "Download" 按钮(本期 UI 不实现,但数据已就绪)。

    - `source_type='telegram'` 当前唯一值,预留 youtube / bilibili 等。
    - `source_url`:人类可读 permalink,浏览器能打开。
    - `source_msg_id` + `source_chat_id`:程序化下载(Telethon client.get_messages)用。
    """

    __tablename__ = "remote_media_reference"

    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(
        Integer,
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    source_type = Column(String(32), nullable=False, default="telegram")
    source_url = Column(Text, nullable=False)
    source_msg_id = Column(Integer, nullable=False)
    source_chat_id = Column(Integer, nullable=True)
    original_filename = Column(String(512), nullable=True)
    original_size = Column(Integer, nullable=True)
    original_mime = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    media = relationship("Media")