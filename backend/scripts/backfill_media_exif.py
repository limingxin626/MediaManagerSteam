"""回填 Media 表的 EXIF / 编码字段。

默认只填空字段(已有值不覆盖)。传 --force 重新覆盖全部。
跳过预览帧(video_media_id IS NOT NULL)。
"""

import os
import sys
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models import SessionLocal, Media
from app.utils import MediaInfoUtils
from app.config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NEW_FIELDS = [
    "taken_at", "gps_lat", "gps_lng", "orientation",
    "camera_make", "camera_model", "lens",
    "video_codec", "audio_codec", "has_audio", "fps", "bitrate",
]


def backfill(force: bool = False, limit: int | None = None):
    db = SessionLocal()
    try:
        q = db.query(Media).filter(Media.video_media_id.is_(None))
        if limit:
            q = q.limit(limit)
        records = q.all()
        total = len(records)
        logger.info(f"待处理 {total} 条 Media")

        updated = skipped = failed = 0
        for idx, m in enumerate(records, 1):
            if not force and all(getattr(m, f) is not None for f in NEW_FIELDS):
                skipped += 1
                continue
            if not m.file_path or not os.path.exists(m.file_path):
                logger.warning(f"[{idx}/{total}] 文件缺失 id={m.id} path={m.file_path}")
                skipped += 1
                continue
            media_type = config.get_media_type(m.file_path)
            if media_type is None:
                skipped += 1
                continue
            try:
                info = MediaInfoUtils.get_media_info(m.file_path, media_type, config.FFPROBE_PATH)
            except Exception as e:
                logger.error(f"[{idx}/{total}] 提取失败 id={m.id}: {e}")
                failed += 1
                continue

            changed = False
            for f in NEW_FIELDS:
                new_val = info.get(f)
                if new_val is None:
                    continue
                if force or getattr(m, f) is None:
                    setattr(m, f, new_val)
                    changed = True
            if changed:
                updated += 1

            if idx % 100 == 0:
                db.commit()
                logger.info(f"  进度 {idx}/{total} (updated={updated})")

        db.commit()
        logger.info("=" * 50)
        logger.info(f"完成: 总计 {total} / 更新 {updated} / 跳过 {skipped} / 失败 {failed}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="覆盖已有值")
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()
    backfill(force=args.force, limit=args.limit)
