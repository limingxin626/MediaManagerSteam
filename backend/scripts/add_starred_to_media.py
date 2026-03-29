import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.models import DATABASE_URL, Base, engine
import shutil

def backup_database():
    db_path = 'db_new.sqlite3'
    backup_path = 'db_new.sqlite3.backup'
    
    if os.path.exists(db_path):
        if os.path.exists(backup_path):
            os.remove(backup_path)
        shutil.copy(db_path, backup_path)
        print(f"数据库已备份到 {backup_path}")
        return True
    else:
        print(f"数据库文件 {db_path} 不存在，无需备份")
        return False

def add_column_if_not_exists(conn, table_name, column_name, column_def):
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result.fetchall()]
    
    if column_name in columns:
        print(f"{table_name}.{column_name} 字段已存在，跳过")
        return False
    
    print(f"添加 {column_name} 字段到 {table_name} 表...")
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"))
    conn.commit()
    
    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    count = result.scalar()
    print(f"已更新 {count} 条 {table_name} 记录")
    return True

def migrate_add_starred():
    db_path = 'db_new.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在，创建新数据库...")
        Base.metadata.create_all(bind=engine)
        print("新数据库已创建，包含 starred 字段")
        return
    
    backup_database()
    
    engine_local = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    with engine_local.connect() as conn:
        media_added = add_column_if_not_exists(conn, 'media', 'starred', 'INTEGER DEFAULT 0 NOT NULL')
        message_added = add_column_if_not_exists(conn, 'message', 'starred', 'INTEGER DEFAULT 0 NOT NULL')
        
        if media_added or message_added:
            print("\n迁移完成！")
        else:
            print("\n所有 starred 字段已存在，无需迁移")

if __name__ == "__main__":
    migrate_add_starred()
