import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import engine
from sqlalchemy import text

def add_indexes():
    """添加分页优化所需的索引"""
    
    indexes = [
        # Message表的索引（用于基于created_at的游标分页）
        "CREATE INDEX IF NOT EXISTS idx_message_created_at_desc ON message(created_at DESC)",
        
        # MessageMedia表的复合索引（用于基于created_at + position的游标分页）
        "CREATE INDEX IF NOT EXISTS idx_message_media_created_position_desc ON message_media(created_at DESC, position DESC)",
        
        # MessageMedia表的message_id索引（用于查询消息关联的媒体）
        "CREATE INDEX IF NOT EXISTS idx_message_media_message_id ON message_media(message_id)",
        
        # MessageMedia表的media_id索引（用于查询媒体关联的消息）
        "CREATE INDEX IF NOT EXISTS idx_message_media_media_id ON message_media(media_id)",
        
        # Media表的created_at索引（用于备用分页）
        "CREATE INDEX IF NOT EXISTS idx_media_created_at_desc ON media(created_at DESC)",
        
        # Actor表的name索引（用于演员搜索）
        "CREATE INDEX IF NOT EXISTS idx_actor_name ON actor(name)",
    ]
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                print(f"✓ Created index: {index_sql}")
            except Exception as e:
                print(f"✗ Failed to create index: {index_sql}")
                print(f"  Error: {e}")
        
        conn.commit()
    
    print("\n" + "="*60)
    print("Index creation completed!")
    print("="*60)

def verify_indexes():
    """验证索引是否创建成功"""
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"))
        indexes = [row[0] for row in result.fetchall()]
        
        print("\nCurrent custom indexes:")
        for index in sorted(indexes):
            print(f"  - {index}")
        
        print(f"\nTotal: {len(indexes)} custom indexes")

if __name__ == "__main__":
    print("="*60)
    print("Adding Pagination Optimization Indexes")
    print("="*60)
    
    add_indexes()
    verify_indexes()
