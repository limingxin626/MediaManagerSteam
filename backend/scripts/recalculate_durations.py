"""
重新计算所有视频/GIF 媒体的 duration。

duration 已改为毫秒单位存储。
此脚本遍历所有 media 记录，重新获取正确的 duration。
"""

import os
import sys
import logging
import mimetypes
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.utils import MediaInfoUtils
from app.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./db_new.sqlite3"


def recalculate_durations():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 查询所有有文件的媒体记录
        result = db.execute(text("""
            SELECT id, file_path, mime_type
            FROM media
            WHERE file_path IS NOT NULL
        """))

        records = result.fetchall()
        total = len(records)

        if total == 0:
            logger.info("没有媒体记录")
            return

        logger.info(f"找到 {total} 条媒体记录")

        updated = 0
        skipped = 0
        failed = 0

        for idx, (media_id, file_path, mime_type) in enumerate(records, 1):
            # 判断媒体类型
            media_type = config.get_media_type(file_path)

            if media_type is None:
                logger.debug(f"[{idx}/{total}] 跳过不支持的类型: {file_path}")
                skipped += 1
                continue

            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.warning(f"[{idx}/{total}] 文件不存在，跳过 ID={media_id}: {file_path}")
                skipped += 1
                continue

            # 获取媒体信息
            media_info = MediaInfoUtils.get_media_info(
                file_path, media_type, config.FFPROBE_PATH
            )

            new_duration = media_info.get("duration")

            if new_duration is None or new_duration <= 0:
                logger.warning(f"[{idx}/{total}] 无法获取 duration: ID={media_id}, 路径={file_path}")
                failed += 1
                continue

            # 更新数据库
            db.execute(
                text("UPDATE media SET duration = :duration WHERE id = :id"),
                {"duration": new_duration, "id": media_id}
            )

            # 每 50 条提交一次
            if idx % 50 == 0:
                db.commit()
                logger.info(f"  已处理并提交 {idx}/{total} 条记录")

            updated += 1

        # 最终提交
        db.commit()

        logger.info("=" * 50)
        logger.info(f"处理完成!")
        logger.info(f"  总计: {total}")
        logger.info(f"  成功更新: {updated}")
        logger.info(f"  跳过(不支持类型/文件不存在): {skipped}")
        logger.info(f"  失败: {failed}")

    except Exception as e:
        db.rollback()
        logger.error(f"发生错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    recalculate_durations()
