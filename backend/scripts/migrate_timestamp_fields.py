import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.models import SessionLocal, Media
from app.config import config

# 原始数据库路径
OLD_DB_PATH = r"E:\django\DjangoWebProject1\db.sqlite3"

def float_to_ms(value):
    """将浮点秒数转换为毫秒整数，如果值为 None 则返回 None"""
    if value is None:
        return None
    return int(round(value * 1000))

def migrate_timestamp_fields():
    print("Starting timestamp fields migration...")
    print("=" * 60)
    
    # 连接原始数据库
    old_engine = create_engine(f"sqlite:///{OLD_DB_PATH}", connect_args={"check_same_thread": False})
    
    # 获取新数据库会话
    new_db = SessionLocal()
    
    try:
        # 从原始数据库读取 media 表数据
        print("Reading data from original database...")
        with old_engine.connect() as conn:
            result = conn.execute(text("SELECT id, startTime, endTime, timestamp, parent_id FROM app_media"))
            old_media_records = result.fetchall()
        
        print(f"Found {len(old_media_records)} records in original database")
        
        # 统计更新数量
        updated_count = 0
        skipped_count = 0
        not_found_count = 0
        
        # 遍历每条记录进行迁移
        for record in old_media_records:
            old_id, start_time, end_time, timestamp, parent_id = record
            
            # 在新数据库中查找对应记录
            new_media = new_db.query(Media).filter(Media.id == old_id).first()
            
            if not new_media:
                not_found_count += 1
                continue
            
            # 准备更新字段
            start_ms = float_to_ms(start_time)
            end_ms = float_to_ms(end_time)
            frame_ms = float_to_ms(timestamp)
            
            # 检查是否有需要更新的内容
            needs_update = False
            
            if new_media.start_ms != start_ms:
                new_media.start_ms = start_ms
                needs_update = True
            
            if new_media.end_ms != end_ms:
                new_media.end_ms = end_ms
                needs_update = True
            
            if new_media.frame_ms != frame_ms:
                new_media.frame_ms = frame_ms
                needs_update = True
            
            # parent_id 映射到 video_media_id
            if new_media.video_media_id != parent_id:
                new_media.video_media_id = parent_id
                needs_update = True
            
            if needs_update:
                updated_count += 1
            else:
                skipped_count += 1
        
        # 批量提交更新
        new_db.commit()
        
        print("=" * 60)
        print("Migration completed!")
        print(f"Updated: {updated_count} records")
        print(f"Skipped (no changes): {skipped_count} records")
        print(f"Not found in new DB: {not_found_count} records")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        new_db.rollback()
        raise
    finally:
        new_db.close()
        old_engine.dispose()

if __name__ == "__main__":
    migrate_timestamp_fields()
