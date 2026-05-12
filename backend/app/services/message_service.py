from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Tag, MessageMedia, message_tag, media_tag


def cleanup_orphan_tags(db: Session) -> int:
    """删除没有任何 message 关联的 tag，返回删除数量。"""
    orphans = (
        db.query(Tag)
        .outerjoin(message_tag, Tag.id == message_tag.c.tag_id)
        .outerjoin(media_tag, Tag.id == media_tag.c.tag_id)
        .group_by(Tag.id)
        .having(
            func.count(message_tag.c.message_id) == 0,
            func.count(media_tag.c.media_id) == 0
        )
        .all()
    )
    for tag in orphans:
        db.delete(tag)
    return len(orphans)


def reorder_message_media(db: Session, message_id: int, media_ids: List[int]) -> bool:
    """按传入的 media_id 顺序重置 MessageMedia.position，返回是否成功。"""
    relations = db.query(MessageMedia).filter(
        MessageMedia.message_id == message_id
    ).all()

    relation_map = {r.media_id: r for r in relations}

    for media_id in media_ids:
        if media_id not in relation_map:
            return False

    for i, r in enumerate(relations):
        r.position = -(i + 1)
    db.flush()

    for pos, media_id in enumerate(media_ids):
        relation_map[media_id].position = pos

    return True
