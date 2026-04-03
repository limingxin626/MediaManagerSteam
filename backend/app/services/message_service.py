import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Message, Tag, MessageMedia, message_tag


def sync_tags_from_text(db: Session, message: Message, text: Optional[str], merge: bool = False) -> None:
    """从 text 中解析 #标签，自动创建不存在的 Tag，并同步 message.tags。

    merge=False（默认）：全量替换，message.tags 只含文本中解析出的标签。
    merge=True：合并模式，保留原有标签，仅添加文本中新增的标签（用于 sync/apply 避免删除手动标签）。
    """
    tag_names = list(dict.fromkeys(re.findall(r'#([\w\u4e00-\u9fff]+)', text or "")))

    text_tags = []
    for name in tag_names:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        text_tags.append(tag)

    if merge:
        # 合并模式：保留现有标签，补充文本中新增的
        existing_ids = {t.id for t in message.tags}
        for tag in text_tags:
            if tag.id not in existing_ids:
                message.tags.append(tag)
    else:
        # 全量替换
        message.tags = text_tags


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
