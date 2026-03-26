import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Message, Tag, MessageMedia, message_tag


def sync_tags_from_text(db: Session, message: Message, text: Optional[str]) -> None:
    """从 text 中解析 #标签，自动创建不存在的 Tag，并全量同步 message.tags。"""
    if not text:
        message.tags = []
        return

    tag_names = list(dict.fromkeys(re.findall(r'#([\w\u4e00-\u9fff]+)', text)))
    if not tag_names:
        message.tags = []
        return

    tags = []
    for name in tag_names:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)

    message.tags = tags


def reorder_message_media(db: Session, message_id: int, media_ids: List[int]) -> bool:
    """按传入的 media_id 顺序重置 MessageMedia.position，返回是否成功。"""
    relations = db.query(MessageMedia).filter(
        MessageMedia.message_id == message_id
    ).all()

    relation_map = {r.media_id: r for r in relations}

    for pos, media_id in enumerate(media_ids):
        if media_id not in relation_map:
            return False
        relation_map[media_id].position = pos

    return True
