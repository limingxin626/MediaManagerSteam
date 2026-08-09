"""Detect and repair stale canonical file paths on Media rows.

By default this script only reports statistics. Pass ``--apply`` to repoint a
stale ``Media.repo_id/file_path`` to one of its completed RepositoryFile rows.
"""

import argparse
import os
import sqlite3
import sys
from collections.abc import Callable
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import config
from app.models import Media, RepositoryFile, SessionLocal


def backup_database(db_path: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{db_path}.pre-media-file-path-repair-{timestamp}.bak"
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


def repair_media_file_paths(
    apply: bool = False,
    sample_limit: int = 10,
    session_factory: Callable = SessionLocal,
) -> dict:
    stats = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "repairable": 0,
        "repaired": 0,
        "without_copy": 0,
        "repair_samples": [],
        "without_copy_samples": [],
    }
    db = session_factory()
    try:
        media_rows = (
            db.query(Media)
            .filter(Media.video_media_id.is_(None))
            .order_by(Media.id)
            .all()
        )
        completed_files = (
            db.query(RepositoryFile)
            .filter(
                RepositoryFile.media_id.is_not(None),
                RepositoryFile.materialize_status == "done",
            )
            .order_by(
                RepositoryFile.media_id,
                RepositoryFile.repo_id,
                RepositoryFile.rel_path,
                RepositoryFile.id,
            )
            .all()
        )

        files_by_media: dict[int, list[RepositoryFile]] = {}
        for row in completed_files:
            files_by_media.setdefault(row.media_id, []).append(row)

        for media in media_rows:
            stats["total"] += 1
            copies = files_by_media.get(media.id, [])
            canonical_valid = any(
                row.repo_id == media.repo_id and row.rel_path == media.file_path
                for row in copies
            )
            if canonical_valid:
                stats["valid"] += 1
                continue

            stats["invalid"] += 1
            if not copies:
                stats["without_copy"] += 1
                if len(stats["without_copy_samples"]) < sample_limit:
                    stats["without_copy_samples"].append({
                        "id": media.id,
                        "repo_id": media.repo_id,
                        "file_path": media.file_path,
                    })
                continue

            replacement = copies[0]
            stats["repairable"] += 1
            if len(stats["repair_samples"]) < sample_limit:
                stats["repair_samples"].append({
                    "id": media.id,
                    "old": f"{media.repo_id}/{media.file_path}",
                    "new": f"{replacement.repo_id}/{replacement.rel_path}",
                })
            if apply:
                media.repo_id = replacement.repo_id
                media.file_path = replacement.rel_path
                stats["repaired"] += 1

        if apply:
            db.commit()
        else:
            db.rollback()
        return stats
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="统计并修复 Media 中已失效的规范 file_path（默认只统计）",
    )
    parser.add_argument("--apply", action="store_true", help="备份后写入数据库；默认仅统计")
    parser.add_argument("--sample-limit", type=int, default=10, help="每类最多输出的样例数")
    args = parser.parse_args()

    if args.sample_limit < 0:
        parser.error("--sample-limit must be >= 0")

    if args.apply:
        backup_path = backup_database(config.get_db_path())
        print(f"backup={backup_path}")

    stats = repair_media_file_paths(apply=args.apply, sample_limit=args.sample_limit)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(
        f"[{mode}] total={stats['total']} valid={stats['valid']} "
        f"invalid={stats['invalid']} repairable={stats['repairable']} "
        f"without_copy={stats['without_copy']} repaired={stats['repaired']}"
    )
    print(f"repair_samples={stats['repair_samples']}")
    print(f"without_copy_samples={stats['without_copy_samples']}")


if __name__ == "__main__":
    main()