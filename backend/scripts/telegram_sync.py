"""Telegram "Saved Messages" → backend 同步 CLI。

子命令:
- bootstrap: 首次交互式登录,生成 .telegram.session(只生成,不做 import)
- backfill:  一次性全量导入(无视 last_message_id)
- once:      单轮增量同步(给 cron 用,完成后退出 0)
- watch:     长驻循环,每 TELEGRAM_POLL_INTERVAL 秒拉一次

环境变量:
- TELEGRAM_API_ID, TELEGRAM_API_HASH:my.telegram.org 申请
- TELEGRAM_SESSION_PATH: 默认 $DATA_ROOT/.telegram.session
- TELEGRAM_INBOX_DIR:    默认 $DATA_ROOT/telegram_inbox/
- TELEGRAM_POLL_INTERVAL: 默认 60 秒
- TELEGRAM_LARGE_FILE_THRESHOLD: 默认 50MB,≥此字节数只下载封面

用法:
    cd backend
    uv run scripts/telegram_sync.py bootstrap   # 首次登录
    uv run scripts/telegram_sync.py backfill    # 全量拉取
    uv run scripts/telegram_sync.py once        # 增量单轮
    uv run scripts/telegram_sync.py watch       # 长驻
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime

# 让 scripts/ 能 import app/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config
from app.models import SessionLocal

from scripts._telegram import client, importer, state

log = logging.getLogger("telegram_sync")


def _setup_logging(verbose: bool = False) -> None:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _check_env() -> None:
    if not config.TELEGRAM_API_ID or not config.TELEGRAM_API_HASH:
        log.error(
            "TELEGRAM_API_ID / TELEGRAM_API_HASH 未设置。"
            "先去 https://my.telegram.org 申请,然后 export。"
        )
        sys.exit(1)


# ── 子命令实现 ─────────────────────────────────────────────────────────────


async def _cmd_bootstrap() -> int:
    log.info("interactive login; follow prompts (phone → code → 2FA)")
    await client.bootstrap()
    print(f"session saved at: {client.session_path()}")
    print("next: python scripts/telegram_sync.py backfill")
    return 0


async def _cmd_cycle() -> int:
    tg_client = await client.connect()
    try:
        db = SessionLocal()
        try:
            stats = await importer.run_cycle(db, tg_client)
        finally:
            db.close()
        print(stats.summary())
        return 0 if stats.errors == 0 else 2
    finally:
        await client.disconnect(tg_client)


async def _cmd_backfill() -> int:
    """一次性全量:把 last_message_id 重置为 0,然后跑一次 once。"""
    db = SessionLocal()
    try:
        state.seed(db)
        row = state.get(db)
        if row.last_message_id > 0:
            log.warning(
                "backfill on already-imported state (last_message_id=%s). "
                "TG 的 min_id=0 仍只返回你账号可见范围内的消息,不会重复导入已 hash-dedup 的文件。",
                row.last_message_id,
            )
        # 不重置 last_message_id —— 用户期望 backfill 是"接续拉满"。
        # 真要从零开始,可以手动 `DELETE FROM telegram_sync_state;`。
    finally:
        db.close()
    return await _cmd_cycle()


async def _cmd_watch() -> int:
    """长驻循环。FloodWait 时退避 sleep;否则按 TELEGRAM_POLL_INTERVAL。"""
    tg_client = await client.connect()
    try:
        while True:
            try:
                db = SessionLocal()
                try:
                    stats = await importer.run_cycle(db, tg_client)
                    log.info(stats.summary())
                finally:
                    db.close()
            except Exception as e:  # noqa: BLE001
                log.exception("cycle crashed")
                try:
                    db2 = SessionLocal()
                    try:
                        state.record_error(db2, repr(e))
                    finally:
                        db2.close()
                except Exception:  # noqa: BLE001
                    log.exception("failed to record error to DB")

            # 计算下次 sleep
            db = SessionLocal()
            try:
                row = state.get(db)
            finally:
                db.close()
            if state.is_in_flood_wait(row) and row.last_flood_wait_until:
                sleep_s = max(
                    1,
                    int((row.last_flood_wait_until - datetime.now()).total_seconds()),
                )
                log.info("sleeping %ds (flood wait)", sleep_s)
            else:
                sleep_s = config.TELEGRAM_POLL_INTERVAL
            await asyncio.sleep(sleep_s)
    finally:
        await client.disconnect(tg_client)


# ── argparse ───────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Sync Telegram Saved Messages to backend DB",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="enable INFO logging (default: WARNING)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bootstrap", help="first-time interactive login (phone+code+2FA)")
    sub.add_parser("backfill", help="one-shot pull, runs once and exits")
    sub.add_parser("once", help="single incremental poll cycle, runs and exits")
    sub.add_parser("watch", help="long-running loop, polls every TELEGRAM_POLL_INTERVAL seconds")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _setup_logging(verbose=args.verbose)
    _check_env()

    if args.cmd == "bootstrap":
        return asyncio.run(_cmd_bootstrap())
    if args.cmd == "backfill":
        return asyncio.run(_cmd_backfill())
    if args.cmd == "once":
        return asyncio.run(_cmd_cycle())
    if args.cmd == "watch":
        return asyncio.run(_cmd_watch())
    parser.error(f"unknown command: {args.cmd}")
    return 1  # unreachable


if __name__ == "__main__":
    sys.exit(main())