#!/usr/bin/env python3
"""把只有一个 media 的 message 的 tag 移到对应的 media 上"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import SessionLocal, Message, MessageMedia, Media, Tag, message_tag, media_tag


def move_tags_to_media():
    db = SessionLocal()

    try:
        # 1. 找出只有一个 media 的 message 及其 media_id
        subquery = (
            select(MessageMedia.message_id, func.count(MessageMedia.media_id).label("media_count"))
            .group_by(MessageMedia.message_id)
            .subquery()
        )

        # 找出 count = 1 的 message_id 和对应的 media_id
        query = (
            select(Message.id, MessageMedia.media_id)
            .join(MessageMedia, Message.id == MessageMedia.message_id)
            .join(subquery, Message.id == subquery.c.message_id)
            .where(subquery.c.media_count == 1)
        )

        single_media_messages = db.execute(query).fetchall()
        print(f"找到 {len(single_media_messages)} 个只有 1 个 media 的 message")

        if not single_media_messages:
            print("没有需要处理的数据")
            return

        # 2. 处理每个 message
        moved_count = 0
        processed_messages = 0

        for msg_id, media_id in single_media_messages:
            # 获取 message 的 tags
            msg = db.query(Message).filter(Message.id == msg_id).first()
            if not msg:
                continue

            tags = list(msg.tags)
            if not tags:
                continue

            processed_messages += 1

            # 获取对应的 media
            media = db.query(Media).filter(Media.id == media_id).first()
            if not media:
                continue

            # 把每个 tag 添加到 media 上
            for tag in tags:
                if tag not in media.tags:
                    media.tags.append(tag)
                    moved_count += 1
                    print(f"  Message {msg_id} -> Media {media_id}: 添加 tag '{tag.name}'")

            # 清除 message 的 tags（设为空列表会触发 relationship 清除）
            msg.tags = []

        # 提交更改
        db.commit()
        print(f"\n处理完成！")
        print(f"  处理了 {processed_messages} 个带 tag 的 message")
        print(f"  共转移了 {moved_count} 个 tag 到 media")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    move_tags_to_media()