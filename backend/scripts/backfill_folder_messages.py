"""Bind existing messages to repository folders by exact media membership.

Dry-run by default. Stop the backend before running this script so the startup
catalog scan cannot create folder-backed messages concurrently.
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import config
from app.models import SessionLocal
from app.modules.repository.folder_message_service import (
    backfill_existing_folder_messages,
    bind_folder_to_existing_message,
)


def backup_database(db_path: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{db_path}.pre-folder-message-backfill-{timestamp}.bak"
    source = sqlite3.connect(db_path)
    try:
        backup = sqlite3.connect(backup_path)
        try:
            source.backup(backup)
        finally:
            backup.close()
    finally:
        source.close()
    return backup_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="按完全相同的 media 集合把已有 message 绑定到 repository folder",
    )
    parser.add_argument("--apply", action="store_true", help="备份后写入；默认 dry-run")
    parser.add_argument("--sample-limit", type=int, default=20, help="每类最多输出的样例数")
    parser.add_argument(
        "--bind",
        action="append",
        default=[],
        metavar="MESSAGE_ID:FOLDER_ID",
        help="显式绑定一个旧 message 与 folder；可重复，仅配合 --apply",
    )
    args = parser.parse_args()
    if args.sample_limit < 0:
        parser.error("--sample-limit must be >= 0")
    if args.bind and not args.apply:
        parser.error("--bind requires --apply")

    explicit_bindings = []
    for value in args.bind:
        try:
            message_id, folder_id = (int(part) for part in value.split(":", 1))
        except (ValueError, TypeError):
            parser.error(f"invalid --bind value: {value!r}; expected MESSAGE_ID:FOLDER_ID")
        explicit_bindings.append((message_id, folder_id))

    if args.apply:
        print(f"backup={backup_database(config.get_db_path())}")

    db = SessionLocal()
    try:
        stats = backfill_existing_folder_messages(
            db,
            apply=args.apply,
            sample_limit=args.sample_limit,
        )
        explicit_changes = 0
        for message_id, folder_id in explicit_bindings:
            explicit_changes += bind_folder_to_existing_message(db, message_id, folder_id)
        if args.apply:
            db.commit()
        else:
            db.rollback()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(
        f"[{mode}] candidate_folders={stats['candidate_folders']} "
        f"matched_folders={stats['matched_folders']} "
        f"matched_messages={stats['matched_messages']} "
        f"already_linked={stats['already_linked']} "
        f"ambiguous_folders={stats['ambiguous_folders']} "
        f"unmatched_folders={stats['unmatched_folders']} "
        f"deleted_generated_messages={stats['deleted_generated_messages']}"
    )
    print(f"explicit_bindings={len(explicit_bindings)} explicit_changes={explicit_changes}")
    print(f"matches={stats['matches']}")
    print(f"ambiguous={stats['ambiguous']}")
    print(f"unmatched={stats['unmatched']}")


if __name__ == "__main__":
    main()
