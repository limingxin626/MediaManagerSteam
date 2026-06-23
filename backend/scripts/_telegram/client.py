"""Telethon 客户端封装。

- bootstrap(): 首次交互式登录(phone → code → 2FA)。
- connect(): 用已有 session 文件连上,失败提示用户跑 bootstrap。
- shutdown(): 断开。

Telethon 是 async 的。调用方在同步入口(asyncio.run)里 await 这些。
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from app.config import config

log = logging.getLogger(__name__)

# Telethon 客户端,延迟 import —— 不在顶层 import,避免无 TG deps 时 import 全失败
_TelethonClient = None
_FloodWaitError = None


def _import_telethon():
    global _TelethonClient, _FloodWaitError
    if _TelethonClient is not None:
        return
    from telethon import TelegramClient  # noqa
    from telethon.errors import FloodWaitError  # noqa

    _TelethonClient = TelegramClient
    _FloodWaitError = FloodWaitError


def session_path() -> str:
    """Telethon session 文件绝对路径(无扩展名也行,Telethon 会自动加 .session)。"""
    p = config.get_telegram_session_path()
    # Telethon 接受不带扩展名的路径,内部会加 .session;为了与 env var 写法一致,
    # 若用户没显式加扩展名,我们也不加。
    return p


def session_exists() -> bool:
    """session 文件是否存在(含 Telethon 自动加的 .session 后缀)。"""
    p = session_path()
    return os.path.exists(p) or os.path.exists(p + ".session")


def make_client() -> "TelegramClient":
    """构造 TelegramClient(未连接)。调用方负责 .start() / .disconnect()。"""
    _import_telethon()
    if not config.TELEGRAM_API_ID or not config.TELEGRAM_API_HASH:
        raise RuntimeError(
            "TELEGRAM_API_ID / TELEGRAM_API_HASH 未设置。"
            "先去 my.telegram.org 申请,然后 export 后再运行。"
        )
    return _TelethonClient(
        session_path(),
        config.TELEGRAM_API_ID,
        config.TELEGRAM_API_HASH,
    )


async def bootstrap() -> None:
    """首次登录:交互式输入 phone + code + 2FA,生成 session 文件。"""
    client = make_client()
    try:
        await client.start()  # 内部会交互式问 phone / code
        me = await client.get_me()
        log.info("bootstrap OK, logged in as %s (id=%s)", me.username, me.id)
    finally:
        await client.disconnect()


async def connect() -> "TelegramClient":
    """连上已有 session;若失败,提示跑 bootstrap。"""
    if not session_exists():
        raise RuntimeError(
            f"未找到 session 文件({session_path()}).请先跑: "
            "python scripts/telegram_sync.py bootstrap"
        )
    client = make_client()
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError(
            "session 已过期或无效,请先跑 bootstrap 重新登录。"
        )
    return client


async def disconnect(client) -> None:
    try:
        await client.disconnect()
    except Exception:  # noqa: BLE001
        log.warning("client.disconnect() raised, ignoring", exc_info=True)