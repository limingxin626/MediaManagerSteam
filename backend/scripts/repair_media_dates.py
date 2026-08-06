"""Clean invalid capture dates and backfill real filesystem creation times."""

import argparse
import os
import sys
from collections.abc import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import config
from app.models import Media, SessionLocal
from app.utils.media_dates import clean_taken_at, get_file_created_at


def repair_media_dates(
    apply: bool = False,
    batch_size: int = 500,
    session_factory: Callable = SessionLocal,
) -> dict:
    stats = {
        "total": 0,
        "epoch_taken_at": 0,
        "file_created_at": 0,
        "missing_file": 0,
        "unresolved_repo": 0,
        "unsupported_creation_time": 0,
        "epoch_sample_ids": [],
        "backfill_sample_ids": [],
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

            for media in media_rows:
                stats["total"] += 1
                if media.taken_at is not None and clean_taken_at(media.taken_at) is None:
                    stats["epoch_taken_at"] += 1
                    if len(stats["epoch_sample_ids"]) < 10:
                        stats["epoch_sample_ids"].append(media.id)
                    if apply:
                        media.taken_at = None

                if media.file_created_at is not None:
                    continue
                absolute_path = config.resolve_to_absolute(media.repo_id, media.file_path)
                if absolute_path is None:
                    stats["unresolved_repo"] += 1
                    continue
                if not os.path.exists(absolute_path):
                    stats["missing_file"] += 1
                    continue
                created_at = get_file_created_at(absolute_path)
                if created_at is None:
                    stats["unsupported_creation_time"] += 1
                    continue

                stats["file_created_at"] += 1
                if len(stats["backfill_sample_ids"]) < 10:
                    stats["backfill_sample_ids"].append(media.id)
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
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    stats = repair_media_dates(apply=args.apply, batch_size=args.batch_size)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] total={stats['total']}")
    print(
        f"epoch_taken_at={stats['epoch_taken_at']} "
        f"sample_ids={stats['epoch_sample_ids']}"
    )
    print(
        f"file_created_at_backfill={stats['file_created_at']} "
        f"sample_ids={stats['backfill_sample_ids']}"
    )
    print(
        f"missing_file={stats['missing_file']} "
        f"unresolved_repo={stats['unresolved_repo']} "
        f"unsupported_creation_time={stats['unsupported_creation_time']}"
    )


if __name__ == "__main__":
    main()
