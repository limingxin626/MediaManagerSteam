#!/usr/bin/env python3
"""查找所有只有一个 media 的 message"""

import sys
import os

# 添加 backend 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import func, select
from app.models import get_db, SessionLocal, Message, MessageMedia, Media


def find_messages_with_single_media():
    """找出只有一个 media 的 message"""
    db = SessionLocal()

    try:
        # 按 message_id 分组统计 media 数量
        subquery = (
            select(MessageMedia.message_id, func.count(MessageMedia.media_id).label("media_count"))
            .group_by(MessageMedia.message_id)
            .subquery()
        )

        # 只取 count = 1 的 message
        query = (
            select(Message.id, Message.text, Message.created_at, subquery.c.media_count)
            .join(subquery, Message.id == subquery.c.message_id)
            .where(subquery.c.media_count == 1)
            .order_by(Message.created_at.desc())
        )

        results = db.execute(query).fetchall()

        print(f"找到 {len(results)} 个只有 1 个 media 的 message：\n")
        print("-" * 80)

        for row in results:
            text_preview = row.text[:50] + "..." if row.text and len(row.text) > 50 else (row.text or "")
            print(f"ID: {row.id:4d} | 创建时间: {row.created_at} | 文本: {text_preview}")

        print("-" * 80)
        print(f"总计: {len(results)} 条")

    finally:
        db.close()


if __name__ == "__main__":
    find_messages_with_single_media()