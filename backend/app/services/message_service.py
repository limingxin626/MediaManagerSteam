from datetime import datetime
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Message, Tag, MessageMedia, message_tag, media_tag
from app.services.media_service import process_file


def cleanup_orphan_tags(db: Session) -> int:
    """删除没有任何 message 关联的 tag，返回删除数量。"""
    orphans = (
        db.query(Tag)
        .outerjoin(message_tag, Tag.id == message_tag.c.tag_id)
        .outerjoin(media_tag, Tag.id == media_tag.c.media_id)
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


def create_message_with_files(
    db: Session,
    text: Optional[str],
    actor_id: Optional[int],
    files: List[str],
    tag_ids: Optional[List[int]] = None,
    created_at: Optional[datetime] = None,
    issue_id: Optional[int] = None,
    commit: bool = True,
) -> Message:
    """创建一个完整 Message(含 N 个 media 文件)。

    是 routers/message.py create_message 的纯 service 层版本,
    不依赖 FastAPI / Pydantic,可供 importer 等非 HTTP 调用者使用。

    Args:
        db: SQLAlchemy session
        text: 消息文本
        actor_id: 作者 ID(None 则 actor_id=NULL)
        files: 文件绝对路径列表,按顺序作为 media(position 0,1,2...)
        tag_ids: 要绑定的 tag ID 列表(None 则不绑)
        created_at: 自定义时间;None 则用 datetime.now()
        issue_id: 关联 issue;None 则不绑
        commit: 是否在函数末尾 commit;False 时由调用者控制事务

    Returns:
        创建的 Message 对象(ID、tags、media 已链接)
    """
    db_message = Message(
        text=text,
        actor_id=actor_id,
        issue_id=issue_id,
        created_at=created_at or datetime.now(),
    )
    db.add(db_message)
    db.flush()

    if tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        db_message.tags = tags

    position = 0
    for file_path in files:
        result = process_file(db, file_path, db_message.id, position)
        if result is not None:
            position += 1

    if commit:
        db.commit()
        db.refresh(db_message)
    return db_message

