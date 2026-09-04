"""回填 Media 表的 EXIF / 编码字段。

默认只填空字段(已有值不覆盖)。传 --force 重新覆盖全部。
跳过预览帧(video_media_id IS NOT NULL)。

路径说明:Media.file_path 是相对 repo 根的 forward-slash 路径(DB 权威),
必须用 config.resolve_to_absolute(repo_id, file_path) 解析成绝对路径再交给
get_media_type / get_media_info;不能直接当成文件系统绝对路径用。
当 canonical 路径已失效(比如文件被搬到另一 repo)时,回退到该 media 名下
materialize_status == 'done' 的 RepositoryFile 物理副本取第一个存在的路径。
"""

import argparse
import logging
import os
import sys
from collections.abc import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import config
from app.models import Media, RepositoryFile, SessionLocal
from app.utils import MediaInfoUtils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NEW_FIELDS = [
    "taken_at", "gps_lat", "gps_lng", "orientation",
    "camera_make", "camera_model", "lens",
    "video_codec", "audio_codec", "has_audio", "fps", "bitrate",
]


def _resolve_physical_path(
    media: Media,
    files_by_media: dict[int, list[RepositoryFile]],
) -> str | None:
    """返回可读的物理绝对路径;找不到返回 None。

    顺序:canonical (repo_id + file_path) > 遗留绝对路径 > RepositoryFile 副本。
    """
    canonical = config.resolve_to_absolute(media.repo_id, media.file_path)
    if canonical and os.path.isfile(canonical):
        return canonical

    # 历史数据里可能有直接存绝对路径的旧行;解析会把它当 repo 相对路径而错乱,
    # 所以先按 isabs 兜一下真实存在的绝对路径。
    if os.path.isabs(media.file_path) and os.path.isfile(media.file_path):
        return media.file_path

    for row in files_by_media.get(media.id, []):
        candidate = config.resolve_to_absolute(row.repo_id, row.rel_path)
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def backfill(
    force: bool = False,
    limit: int | None = None,
    batch_size: int = 200,
    session_factory: Callable = SessionLocal,
) -> dict:
    db = session_factory()
    stats = {
        "total": 0,
        "updated": 0,
        "already_complete": 0,
        "missing_file": 0,
        "unsupported_type": 0,
        "extract_failed": 0,
    }
    try:
        last_id = 0
        processed = 0
        while True:
            q = (
                db.query(Media)
                .filter(
                    Media.id > last_id,
                    Media.video_media_id.is_(None),
                )
                .order_by(Media.id)
                .limit(batch_size)
            )
            records = q.all()
            if not records:
                break
            last_id = records[-1].id

            media_ids = [m.id for m in records]
            files = (
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
            for row in files:
                files_by_media.setdefault(row.media_id, []).append(row)

            for idx, m in enumerate(records, 1):
                stats["total"] += 1
                if not force and all(getattr(m, f) is not None for f in NEW_FIELDS):
                    stats["already_complete"] += 1
                    continue

                abs_path = _resolve_physical_path(m, files_by_media)
                if abs_path is None:
                    logger.warning(f"[{m.id}] 文件缺失 repo={m.repo_id} path={m.file_path}")
                    stats["missing_file"] += 1
                    continue

                media_type = config.get_media_type(abs_path)
                if media_type is None:
                    logger.warning(f"[{m.id}] 不支持的扩展名 path={m.file_path}")
                    stats["unsupported_type"] += 1
                    continue

                try:
                    info = MediaInfoUtils.get_media_info(abs_path, media_type, config.FFPROBE_PATH)
                except Exception as e:
                    logger.error(f"[{m.id}] 提取失败 path={m.file_path}: {e}")
                    stats["extract_failed"] += 1
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
                    stats["updated"] += 1

            db.commit()
            processed += len(records)
            logger.info(
                f"进度 {processed} 条 (updated={stats['updated']})"
            )
            if limit is not None and processed >= limit:
                break
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="回填 Media 的 EXIF / 编码元数据")
    parser.add_argument("--force", action="store_true", help="覆盖已有值;默认只填空字段")
    parser.add_argument("--limit", type=int, default=None, help="最多处理多少条(用于测试)")
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()

    stats = backfill(
        force=args.force,
        limit=args.limit,
        batch_size=args.batch_size,
    )
    logger.info(
        "完成: 总计 %(total)d / 更新 %(updated)d / 已完整跳过 %(already_complete)d "
        "/ 缺文件 %(missing_file)d / 不支持 %(unsupported_type)d / 失败 %(extract_failed)d",
        stats,
    )


if __name__ == "__main__":
    main()
