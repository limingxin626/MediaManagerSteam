import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Message, Media, MessageMedia
from datetime import datetime

def test_message_cursor_pagination():
    """测试Message的游标分页"""
    print("="*60)
    print("Testing Message Cursor Pagination")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # 第一页：不提供游标
        print("\nPage 1 (no cursor):")
        query = db.query(Message).order_by(Message.created_at.desc()).limit(21).all()
        has_more = len(query) > 20
        items = query[:20]
        next_cursor = items[-1].created_at.isoformat() if has_more and items else None
        
        print(f"  Items: {len(items)}")
        print(f"  Has more: {has_more}")
        print(f"  Next cursor: {next_cursor}")
        print(f"  First message: ID={items[0].id}, created_at={items[0].created_at}")
        print(f"  Last message: ID={items[-1].id}, created_at={items[-1].created_at}")
        
        # 第二页：使用游标
        if next_cursor:
            print(f"\nPage 2 (cursor: {next_cursor}):")
            cursor_time = datetime.fromisoformat(next_cursor)
            query = db.query(Message).filter(
                Message.created_at < cursor_time
            ).order_by(Message.created_at.desc()).limit(21).all()
            
            has_more = len(query) > 20
            items = query[:20]
            next_cursor = items[-1].created_at.isoformat() if has_more and items else None
            
            print(f"  Items: {len(items)}")
            print(f"  Has more: {has_more}")
            print(f"  Next cursor: {next_cursor}")
            print(f"  First message: ID={items[0].id}, created_at={items[0].created_at}")
            print(f"  Last message: ID={items[-1].id}, created_at={items[-1].created_at}")
    
    finally:
        db.close()

def test_media_cursor_pagination():
    """测试Media的游标分页（基于MessageMedia）"""
    print("\n" + "="*60)
    print("Testing Media Cursor Pagination (MessageMedia-based)")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # 第一页：不提供游标
        print("\nPage 1 (no cursor):")
        query = db.query(Media).join(MessageMedia).order_by(
            MessageMedia.created_at.desc(), 
            MessageMedia.position.desc()
        ).limit(21).all()
        
        has_more = len(query) > 20
        items = query[:20]
        
        # 获取最后一个media对应的MessageMedia信息
        next_cursor = None
        if has_more and items:
            last_media_id = items[-1].id
            last_mm = db.query(MessageMedia).filter(
                MessageMedia.media_id == last_media_id
            ).order_by(MessageMedia.created_at.desc()).first()
            if last_mm:
                next_cursor = f"{last_mm.created_at.isoformat()}|{last_mm.position}"
        
        print(f"  Items: {len(items)}")
        print(f"  Has more: {has_more}")
        print(f"  Next cursor: {next_cursor}")
        print(f"  First media: ID={items[0].id}, created_at={items[0].created_at}")
        print(f"  Last media: ID={items[-1].id}, created_at={items[-1].created_at}")
        
        # 第二页：使用游标
        if next_cursor:
            print(f"\nPage 2 (cursor: {next_cursor}):")
            parts = next_cursor.split('|')
            cursor_time = datetime.fromisoformat(parts[0])
            cursor_position = int(parts[1])
            
            query = db.query(Media).join(MessageMedia).filter(
                (MessageMedia.created_at < cursor_time) | 
                ((MessageMedia.created_at == cursor_time) & (MessageMedia.position < cursor_position))
            ).order_by(
                MessageMedia.created_at.desc(), 
                MessageMedia.position.desc()
            ).limit(21).all()
            
            has_more = len(query) > 20
            items = query[:20]
            
            next_cursor = None
            if has_more and items:
                last_media_id = items[-1].id
                last_mm = db.query(MessageMedia).filter(
                    MessageMedia.media_id == last_media_id
                ).order_by(MessageMedia.created_at.desc()).first()
                if last_mm:
                    next_cursor = f"{last_mm.created_at.isoformat()}|{last_mm.position}"
            
            print(f"  Items: {len(items)}")
            print(f"  Has more: {has_more}")
            print(f"  Next cursor: {next_cursor}")
            print(f"  First media: ID={items[0].id}, created_at={items[0].created_at}")
            print(f"  Last media: ID={items[-1].id}, created_at={items[-1].created_at}")
    
    finally:
        db.close()

def test_performance_comparison():
    """对比offset和cursor的性能"""
    print("\n" + "="*60)
    print("Performance Comparison: Offset vs Cursor")
    print("="*60)
    
    import time
    
    db = SessionLocal()
    
    try:
        # 测试offset分页（第100页）
        print("\nOffset pagination (page 100, skip=2000):")
        start_time = time.time()
        query = db.query(Message).order_by(Message.created_at.desc()).offset(2000).limit(20).all()
        offset_time = time.time() - start_time
        print(f"  Time: {offset_time:.4f}s")
        print(f"  Items: {len(query)}")
        
        # 测试cursor分页（第100页）
        print("\nCursor pagination (page 100):")
        
        # 先获取前99页的最后一个cursor
        cursor = None
        for page in range(99):
            if cursor:
                cursor_time = datetime.fromisoformat(cursor)
                query = db.query(Message).filter(
                    Message.created_at < cursor_time
                ).order_by(Message.created_at.desc()).limit(21).all()
            else:
                query = db.query(Message).order_by(Message.created_at.desc()).limit(21).all()
            
            has_more = len(query) > 20
            items = query[:20]
            cursor = items[-1].created_at.isoformat() if has_more and items else None
            
            if not cursor:
                break
        
        if cursor:
            start_time = time.time()
            cursor_time = datetime.fromisoformat(cursor)
            query = db.query(Message).filter(
                Message.created_at < cursor_time
            ).order_by(Message.created_at.desc()).limit(20).all()
            cursor_time_elapsed = time.time() - start_time
            print(f"  Time: {cursor_time_elapsed:.4f}s")
            print(f"  Items: {len(query)}")
            print(f"  Speedup: {offset_time / cursor_time_elapsed:.2f}x")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_message_cursor_pagination()
    test_media_cursor_pagination()
    test_performance_comparison()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
