"""
修复图片 EXIF orientation 导致 width/height 反转的存量数据。

历史 bug: get_media_info 读 PIL Image.size 时未应用 EXIF orientation,
导致竖屏拍摄的照片在数据库里 width/height 是横向的。
此脚本只处理 image 类型,重新读取并应用 exif_transpose 后更新尺寸。
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PIL import Image, ImageOps
from app.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./db_new.sqlite3"


def fix_image_orientation():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        result = db.execute(text("""
            SELECT id, file_path, width, height
            FROM media
            WHERE file_path IS NOT NULL
        """))
        records = result.fetchall()
        total = len(records)
        logger.info(f"共 {total} 条媒体记录")

        updated = 0
        skipped = 0
        failed = 0
        unchanged = 0

        for idx, (media_id, file_path, old_w, old_h) in enumerate(records, 1):
            media_type = config.get_media_type(file_path)
            if media_type != "IMAGE":
                skipped += 1
                continue

            if not os.path.exists(file_path):
                logger.warning(f"[{idx}/{total}] 文件不存在 ID={media_id}: {file_path}")
                skipped += 1
                continue

            try:
                with Image.open(file_path) as img:
                    transposed = ImageOps.exif_transpose(img)
                    new_w, new_h = transposed.size
            except Exception as e:
                logger.error(f"[{idx}/{total}] 读取失败 ID={media_id}: {e}")
                failed += 1
                continue

            if new_w == old_w and new_h == old_h:
                unchanged += 1
                continue

            db.execute(
                text("UPDATE media SET width = :w, height = :h WHERE id = :id"),
                {"w": new_w, "h": new_h, "id": media_id}
            )
            logger.info(f"[{idx}/{total}] ID={media_id}: {old_w}x{old_h} -> {new_w}x{new_h}")
            updated += 1

            if updated % 50 == 0:
                db.commit()

        db.commit()
        logger.info("=" * 50)
        logger.info(f"处理完成! 更新={updated} 未变={unchanged} 跳过={skipped} 失败={failed}")

    finally:
        db.close()


if __name__ == "__main__":
    fix_image_orientation()
