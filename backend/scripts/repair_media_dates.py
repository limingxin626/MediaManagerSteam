"""Clean invalid capture dates and repair filesystem fallback dates."""

import argparse
import os
import sqlite3
import sys
from collections.abc import Callable
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import config
from app.models import Media, RepositoryFile, SessionLocal
from app.utils.media_dates import clean_taken_at, get_file_created_at


def backup_database(db_path: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{db_path}.pre-media-date-rebackfill-{timestamp}.bak"
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


def repair_media_dates(
    apply: bool = False,
    batch_size: int = 500,
    overwrite_existing: bool = False,
    session_factory: Callable = SessionLocal,
) -> dict:
    stats = {
        "total": 0,
        "taken_at_present": 0,
        "taken_at_missing": 0,
        "epoch_taken_at": 0,
        "file_created_at_present": 0,
        "file_created_at_missing": 0,
        "file_created_at": 0,
        "file_created_at_filled": 0,
        "file_created_at_corrected": 0,
        "file_created_at_unchanged": 0,
        "physical_copy_fallback": 0,
        "missing_file": 0,
        "unresolved_repo": 0,
        "unsupported_creation_time": 0,
        "epoch_sample_ids": [],
        "backfill_sample_ids": [],
        "correction_samples": [],
        "physical_copy_fallback_samples": [],
        "missing_file_samples": [],
        "unresolved_repo_samples": [],
    }
    db = session_factory()
    try:
        last_id = 0
        while True:
            media_rows = (
                db.query(Media)
                .filter(Media.id > last_id)
                .order_by(Media.id)
                .limit(batch_size)
                .all()
            )
            if not media_rows:
                break

            media_ids = [media.id for media in media_rows]
            completed_files = (
                db.query(RepositoryFile)
                .filter(
                    RepositoryFile.media_id.in_(media_ids),
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
                if media.taken_at is None:
                    stats["taken_at_missing"] += 1
                else:
                    stats["taken_at_present"] += 1
                if media.taken_at is not None and clean_taken_at(media.taken_at) is None:
                    stats["epoch_taken_at"] += 1
                    if len(stats["epoch_sample_ids"]) < 10:
                        stats["epoch_sample_ids"].append(media.id)
                    if apply:
                        media.taken_at = None

                if media.file_created_at is None:
                    stats["file_created_at_missing"] += 1
                else:
                    stats["file_created_at_present"] += 1
                if media.file_created_at is not None and not overwrite_existing:
                    continue
                absolute_path = config.resolve_to_absolute(media.repo_id, media.file_path)
                canonical_path = absolute_path
                if absolute_path is None or not os.path.isfile(absolute_path):
                    absolute_path = next(
                        (
                            candidate
                            for row in files_by_media.get(media.id, [])
                            if (candidate := config.resolve_to_absolute(row.repo_id, row.rel_path))
                            and os.path.isfile(candidate)
                        ),
                        None,
                    )
                    if absolute_path is not None:
                        stats["physical_copy_fallback"] += 1
                        if len(stats["physical_copy_fallback_samples"]) < 10:
                            stats["physical_copy_fallback_samples"].append({
                                "id": media.id,
                                "canonical_path": canonical_path,
                                "physical_path": absolute_path,
                            })

                if absolute_path is None and canonical_path is None:
                    stats["unresolved_repo"] += 1
                    if len(stats["unresolved_repo_samples"]) < 10:
                        stats["unresolved_repo_samples"].append({
                            "id": media.id,
                            "repo_id": media.repo_id,
                            "file_path": media.file_path,
                        })
                    continue
                if absolute_path is None:
                    stats["missing_file"] += 1
                    if len(stats["missing_file_samples"]) < 10:
                        stats["missing_file_samples"].append({
                            "id": media.id,
                            "path": canonical_path,
                        })
                    continue
                created_at = get_file_created_at(absolute_path)
                if created_at is None:
                    stats["unsupported_creation_time"] += 1
                    continue

                old_value = media.file_created_at
                if old_value == created_at:
                    stats["file_created_at_unchanged"] += 1
                    continue

                stats["file_created_at"] += 1
                if old_value is None:
                    stats["file_created_at_filled"] += 1
                    if len(stats["backfill_sample_ids"]) < 10:
                        stats["backfill_sample_ids"].append(media.id)
                else:
                    stats["file_created_at_corrected"] += 1
                    if len(stats["correction_samples"]) < 10:
                        stats["correction_samples"].append({
                            "id": media.id,
                            "old": old_value.isoformat(sep=" "),
                            "new": created_at.isoformat(sep=" "),
                            "path": absolute_path,
                        })
                if apply:
                    media.file_created_at = created_at

            last_id = media_rows[-1].id
            if apply:
                db.commit()
            else:
                db.expunge_all()

        if not apply:
            db.rollback()
        return stats
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="写入数据库；默认仅预览")
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="按当前规则重新计算已有 file_created_at；默认仅补空值",
    )
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    if args.apply:
        backup_path = backup_database(config.get_db_path())
        print(f"backup={backup_path}")

    print(f"database={config.get_db_path()}")
    stats = repair_media_dates(
        apply=args.apply,
        batch_size=args.batch_size,
        overwrite_existing=args.overwrite_existing,
    )
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] total={stats['total']} overwrite_existing={args.overwrite_existing}")
    print(
        f"taken_at_present={stats['taken_at_present']} "
        f"taken_at_missing={stats['taken_at_missing']} "
        f"epoch_taken_at={stats['epoch_taken_at']} "
        f"sample_ids={stats['epoch_sample_ids']}"
    )
    print(
        f"file_created_at_present={stats['file_created_at_present']} "
        f"file_created_at_missing={stats['file_created_at_missing']} "
        f"changed={stats['file_created_at']} "
        f"filled={stats['file_created_at_filled']} "
        f"corrected={stats['file_created_at_corrected']} "
        f"unchanged={stats['file_created_at_unchanged']} "
        f"filled_sample_ids={stats['backfill_sample_ids']}"
    )
    print(f"correction_samples={stats['correction_samples']}")
    print(
        f"physical_copy_fallback={stats['physical_copy_fallback']} "
        f"samples={stats['physical_copy_fallback_samples']}"
    )
    print(
        f"missing_file={stats['missing_file']} "
        f"unresolved_repo={stats['unresolved_repo']} "
        f"unsupported_creation_time={stats['unsupported_creation_time']}"
    )
    print(f"missing_file_samples={stats['missing_file_samples']}")
    print(f"unresolved_repo_samples={stats['unresolved_repo_samples']}")


if __name__ == "__main__":
    main()
