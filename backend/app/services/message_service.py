from datetime import datetime, timedelta
from typing import Callable, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Message, Tag, MessageMedia, message_tag, media_tag
from app.services.media_service import process_file


def cleanup_orphan_tags(db: Session, commit: bool = True) -> int:
    """删除没有任何 message 关联的 tag，返回删除数量。
    commit=True (默认) 时函数末尾 commit;False 时由调用者控制事务边界。"""
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
    if commit:
        db.commit()
    return len(orphans)


def reorder_message_media(db: Session, message_id: int, media_ids: List[int], commit: bool = True) -> bool:
    """按传入的 media_id 顺序重置 MessageMedia.position，返回是否成功。
    commit=True (默认) 时函数末尾 commit;False 时由调用者控制事务边界。"""
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

    if commit:
        db.commit()
    return True


def link_media_to_message(db: Session, message_id: int, media_id: int, position: int) -> None:
    """Link a Media to a Message at the given position.

    Caller is responsible for computing position (max(existing)+1 for appending,
    or 0..N-1 for new message creation). Does not flush — the caller's
    transaction boundary controls persistence.
    """
    db.add(MessageMedia(message_id=message_id, media_id=media_id, position=position))


def get_message(db: Session, message_id: int) -> Optional[Message]:
    """按 id 查 message,薄层,提供给 router 一个不直接 import model 的入口。"""
    return db.query(Message).filter(Message.id == message_id).first()


def create_message_service(
    db: Session,
    text: Optional[str],
    actor_id: Optional[int],
    files: List[str],
    tag_ids: Optional[List[int]] = None,
    created_at: Optional[datetime] = None,
    issue_id: Optional[int] = None,
    client_id: Optional[int] = None,
    media_id_resolver: Optional[Callable[[int], Optional[int]]] = None,
    commit: bool = True,
) -> Message:
    """统一创建 message + files 的 service(收敛 create_message / create_message_from_client)。

    - client_id: 若提供且已存在,返回已存在的 Message(不重新插入)。供 Android sync 幂等。
    - media_id_resolver: Optional[Callable[[file_index], Optional[int]],用于客户端主导的 media_id。
      与 process_file 的 media_id 参数配合。

    Raises:
        ValueError: 客户端 ID 已冲突(罕见,client_id != None 且已存在但 ID 不在请求里时)
    """
    if client_id is not None:
        existing = db.query(Message).filter(Message.id == client_id).first()
        if existing is not None:
            return existing

    db_message = Message(
        text=text,
        actor_id=actor_id,
        issue_id=issue_id,
        created_at=created_at or datetime.now(),
    )
    if client_id is not None:
        db_message.id = client_id
    db.add(db_message)
    db.flush()

    if tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        db_message.tags = tags

    position = 0
    for idx, file_path in enumerate(files):
        media_id_arg = media_id_resolver(idx) if media_id_resolver else None
        result = process_file(db, file_path, media_id=media_id_arg, commit=False)
        if result is not None:
            link_media_to_message(db, db_message.id, result["media"].id, position)
            position += 1

    if commit:
        db.commit()
        db.refresh(db_message)
    return db_message


def update_message_service(
    db: Session,
    message_id: int,
    text: Optional[str] = None,
    actor_id: Optional[int] = None,
    issue_id: Optional[int] = None,
    starred: Optional[bool] = None,
    created_at: Optional[datetime] = None,
    tag_ids: Optional[List[int]] = None,
    media_order: Optional[List[int]] = None,
    commit: bool = True,
) -> Optional[Message]:
    """更新 message 字段。None 参数表示不修改该字段。

    - tag_ids: 显式 tag 列表;若传空 list 则清空所有 tag
    - media_order: 重排 MessageMedia.position

    Returns:
        更新后的 Message,若 message_id 不存在返回 None
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if message is None:
        return None

    if text is not None:
        message.text = text

    if tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all() if tag_ids else []
        message.tags = tags

    if actor_id is not None:
        message.actor_id = actor_id

    if issue_id is not None:
        message.issue_id = issue_id if issue_id != 0 else None

    if starred is not None:
        message.starred = 1 if starred else 0

    if created_at is not None:
        message.created_at = created_at

    if media_order is not None:
        if not reorder_message_media(db, message_id, media_order, commit=False):
            raise ValueError("media_order 包含不属于该消息的 media_id")

    if commit:
        db.commit()
        db.refresh(message)
    return message


def delete_message_service(
    db: Session,
    message_id: int,
    commit: bool = True,
) -> bool:
    """删除一条 message,顺带清理 orphan tag。返回是否成功删除。"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if message is None:
        return False

    db.delete(message)
    cleanup_orphan_tags(db, commit=False)

    if commit:
        db.commit()
    return True


def merge_messages_service(
    db: Session,
    message_ids: List[int],
    commit: bool = True,
) -> Optional[Message]:
    """把多条 message 合并到最早一条(按 created_at 升序)。

    业务:
    - 文本用 '\\n' 拼接
    - MessageMedia 按 position 顺序 reparent 到 target,从 max(target)+1 开始
    - tag union 去重
    - 其余 message 删除
    - 单个 transaction 内完成(若 commit=True)

    Raises:
        ValueError: ids 少于 2 / 有 id 找不到
    """
    if len(message_ids) < 2:
        raise ValueError("至少需要两条消息才能合并")

    msgs = (
        db.query(Message)
        .filter(Message.id.in_(message_ids))
        .order_by(Message.created_at.asc())
        .all()
    )
    if len(msgs) != len(message_ids):
        raise ValueError("部分消息不存在")

    target = msgs[0]
    others = msgs[1:]

    # 合并文本
    texts = [m.text for m in msgs if m.text]
    if texts:
        target.text = "\n".join(texts)

    # 合并媒体:把其他消息的 media 接到 target 后面
    max_pos = (
        db.query(func.coalesce(func.max(MessageMedia.position), -1))
        .filter(MessageMedia.message_id == target.id)
        .scalar()
    )
    next_pos = max_pos + 1

    for other in others:
        relations = sorted(list(other.message_media), key=lambda r: r.position)
        for rel in relations:
            other.message_media.remove(rel)
            rel.message_id = target.id
            rel.position = next_pos
            target.message_media.append(rel)
            next_pos += 1

    # 合并 tags(去重)
    all_tags = {t.id: t for t in target.tags}
    for other in others:
        for t in other.tags:
            all_tags[t.id] = t
        other.tags = []
    target.tags = list(all_tags.values())

    db.flush()

    # 删除其余消息
    for other in others:
        db.delete(other)

    if commit:
        db.commit()
        db.refresh(target)
    return target


def split_message_service(
    db: Session,
    source_message_id: int,
    new_message_id: int,
    new_text: str,
    media_ids: List[int],
    commit: bool = True,
) -> Optional[Message]:
    """把选中的 media 从 source 拆到一条新 message。继承 source 的 tag/actor/starred。

    - new_message_id: 客户端提供的 id(用于 Android sync 幂等)
    - new_text: 新 message 的文本
    - media_ids: 要拆走的 media_id 子集;不能是 source 全部 media
    - 推断 created_at: source.created_at + (nearby_count + 1) seconds

    Raises:
        ValueError: source 找不到 / media_ids 不属于 source / 拆全部
    """
    source = db.query(Message).filter(Message.id == source_message_id).first()
    if not source:
        raise ValueError("Message not found")

    media_ids_set = set(media_ids)
    relations = (
        db.query(MessageMedia)
        .filter(MessageMedia.message_id == source_message_id)
        .order_by(MessageMedia.position)
        .all()
    )
    source_media_ids = {r.media_id for r in relations}
    if not media_ids_set.issubset(source_media_ids):
        raise ValueError("部分 media_id 不属于该消息")
    if len(media_ids_set) == len(relations):
        raise ValueError("不能拆分全部媒体,至少保留一个")

    nearby_count = (
        db.query(func.count(Message.id))
        .filter(
            Message.created_at > source.created_at,
            Message.created_at <= source.created_at + timedelta(seconds=30),
        )
        .scalar()
    )

    new_msg = Message(
        id=new_message_id,
        text=new_text,
        actor_id=source.actor_id,
        starred=source.starred,
        created_at=source.created_at + timedelta(seconds=nearby_count + 1),
    )
    db.add(new_msg)
    db.flush()

    # 复制 tags
    for tag in source.tags:
        new_msg.tags.append(tag)

    # 移动选中的 media 到新 message,重新编号 position
    new_pos = 0
    src_pos = 0
    for rel in relations:
        if rel.media_id in media_ids_set:
            rel.message_id = new_msg.id
            rel.position = new_pos
            new_pos += 1
        else:
            rel.position = src_pos
            src_pos += 1

    if commit:
        db.commit()
        db.refresh(new_msg)
    return new_msg


def add_media_to_message_service(
    db: Session,
    message_id: int,
    file_paths: List[str],
    commit: bool = True,
) -> int:
    """追加 N 个文件到 message,position 从 max(existing)+1 开始。

    Returns:
        新创建/链接的 media 数(跳过 missing / 不支持类型的文件)

    Raises:
        ValueError: message_id 不存在
    """
    if not db.query(Message).filter(Message.id == message_id).first():
        raise ValueError("Message not found")

    max_pos = (
        db.query(func.coalesce(func.max(MessageMedia.position), -1))
        .filter(MessageMedia.message_id == message_id)
        .scalar()
    )
    position = max_pos + 1

    linked = 0
    for file_path in file_paths:
        result = process_file(db, file_path, commit=False)
        if result is not None:
            link_media_to_message(db, message_id, result["media"].id, position)
            position += 1
            linked += 1

    if commit:
        db.commit()
    return linked


def remove_media_from_message_service(
    db: Session,
    message_id: int,
    media_id: int,
    commit: bool = True,
) -> bool:
    """解除一条 MessageMedia 关联,然后对剩余 position 重新连续编号(0..N-1)。

    Returns:
        是否执行了删除(原 relation 存在)

    Raises:
        ValueError: message_id 不存在
    """
    if not db.query(Message).filter(Message.id == message_id).first():
        raise ValueError("Message not found")

    relation = (
        db.query(MessageMedia)
        .filter(MessageMedia.message_id == message_id, MessageMedia.media_id == media_id)
        .first()
    )
    if not relation:
        return False

    db.delete(relation)
    db.flush()  # 确保 deleted 反映到 DB,后续 remaining 查询不会拿到它

    remaining = (
        db.query(MessageMedia)
        .filter(MessageMedia.message_id == message_id)
        .order_by(MessageMedia.position)
        .all()
    )
    for i, rel in enumerate(remaining):
        rel.position = i

    if commit:
        db.commit()
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
        # commit=False 避免循环内多次 commit;末尾由本函数的 commit 参数统一决定
        result = process_file(db, file_path, commit=False)
        if result is not None:
            link_media_to_message(db, db_message.id, result["media"].id, position)
            position += 1

    if commit:
        db.commit()
        db.refresh(db_message)
    return db_message

