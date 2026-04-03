"""
为使用文件大小作为 hash 的媒体记录重新计算 hash。

之前 >100MB 文件的 file_hash 存的是文件大小字符串，现在改为采样哈希。
此脚本查找所有 file_hash 为纯数字且等于 file_size 的记录，重新计算 hash。
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.utils import calculate_file_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./db_new.sqlite3"


def recalculate_hashes():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 查询所有需要更新的记录
        result = db.execute(text("""
            SELECT id, file_path, file_hash, file_size
            FROM media
            WHERE file_hash GLOB '[0-9]*' AND CAST(file_hash AS INTEGER) = file_size
        """))

        records = result.fetchall()
        total = len(records)

        if total == 0:
            logger.info("没有需要更新的记录")
            return

        logger.info(f"找到 {total} 条需要重新计算 hash 的记录")

        updated = 0
        skipped = 0
        failed = 0

        for idx, (media_id, file_path, old_hash, file_size) in enumerate(records, 1):
            logger.info(f"[{idx}/{total}] 处理 ID={media_id}, 路径={file_path}")

            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.warning(f"  文件不存在，跳过: {file_path}")
                skipped += 1
                continue

            # 重新计算 hash
            new_hash = calculate_file_hash(file_path)

            if new_hash is None:
                logger.error(f"  计算 hash 失败: {file_path}")
                failed += 1
                continue

            # 检查是否有其他记录已经使用了这个新 hash
            existing = db.execute(
                text("SELECT id, file_path FROM media WHERE file_hash = :hash AND id != :id"),
                {"hash": new_hash, "id": media_id}
            ).fetchone()

            if existing:
                existing_id, existing_path = existing
                logger.warning(f"  新 hash 与现有记录冲突!")
                logger.warning(f"    当前记录: ID={media_id}, 路径={file_path}")
                logger.warning(f"    现有记录: ID={existing_id}, 路径={existing_path}")
                logger.warning(f"    这可能是之前错误合并的文件，需要手动处理")
                skipped += 1
                continue

            # 更新数据库
            db.execute(
                text("UPDATE media SET file_hash = :new_hash WHERE id = :id"),
                {"new_hash": new_hash, "id": media_id}
            )

            logger.info(f"  已更新: {old_hash} -> {new_hash[:16]}...")
            updated += 1

            # 每 10 条提交一次
            if idx % 10 == 0:
                db.commit()
                logger.info(f"  已提交 {idx} 条记录")

        # 最终提交
        db.commit()

        logger.info("=" * 50)
        logger.info(f"处理完成!")
        logger.info(f"  总计: {total}")
        logger.info(f"  成功更新: {updated}")
        logger.info(f"  跳过(文件不存在): {skipped}")
        logger.info(f"  失败: {failed}")

    except Exception as e:
        db.rollback()
        logger.error(f"发生错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    recalculate_hashes()
