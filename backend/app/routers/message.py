from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import get_db, Message, MessageMedia, message_tag
from app.schemas.message import (
    MessageCreate, MessageUpdate, MessageMerge,
    MessageResponse, MessageDetailResponse,
    MessageMediaItem, MessageTagItem,
    CursorResponse, MessageDetailCursorResponse,
    MessageDateCount, MessageDatesResponse,
    MessageSyncMediaItem, MessageSyncResponse,
    MEDIA_PREVIEW_LIMIT,
)
from app.services.message_service import sync_tags_from_text, reorder_message_media
from app.services.media_service import process_file

router = APIRouter(prefix="/messages", tags=["messages"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_cursor(cursor: Optional[str]) -> Optional[datetime]:
    if not cursor:
        return None
    try:
        return datetime.fromisoformat(cursor)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid cursor format")


def _build_detail_query(
    db: Session,
    actor_id: Optional[int],
    query_text: Optional[str],
    media_id: Optional[int],
    tag_id: Optional[int],
    starred: Optional[bool] = None,
):
    """공통 필터만 적용한 Message 쿼리를 반환 (정렬·커서 없음)."""
    query = db.query(Message)
    if actor_id:
        query = query.filter(Message.actor_id == actor_id)
    if query_text:
        query = query.filter(Message.text.ilike(f"%{query_text}%"))
    if media_id:
        query = query.join(MessageMedia).filter(MessageMedia.media_id == media_id)
    if tag_id:
        query = query.join(message_tag, Message.id == message_tag.c.message_id).filter(
            message_tag.c.tag_id == tag_id
        )
    if starred is not None:
        query = query.filter(Message.starred == (1 if starred else 0))
    return query


def _build_message_query(
    db: Session,
    actor_id: Optional[int],
    query_text: Optional[str],
    media_id: Optional[int],
    tag_id: Optional[int],
    cursor_time: Optional[datetime],
    starred: Optional[bool] = None,
):
    """공통 필터·정렬을 적용한 Message 쿼리를 반환한다."""
    query = db.query(Message)

    if actor_id:
        query = query.filter(Message.actor_id == actor_id)
    if query_text:
        query = query.filter(Message.text.ilike(f"%{query_text}%"))
    if media_id:
        query = query.join(MessageMedia).filter(MessageMedia.media_id == media_id)
    if tag_id:
        query = query.join(message_tag, Message.id == message_tag.c.message_id).filter(
            message_tag.c.tag_id == tag_id
        )
    if starred is not None:
        query = query.filter(Message.starred == (1 if starred else 0))
    if cursor_time:
        query = query.filter(Message.created_at < cursor_time)

    return query.order_by(Message.created_at.desc())


def _paginate(query, limit: int):
    """返回 (items, has_more, next_cursor)。"""
    rows = query.limit(limit + 1).all()
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = items[-1].created_at.isoformat() if has_more and items else None
    return items, has_more, next_cursor


def _media_items_for(db: Session, message_id: int, limit: Optional[int] = MEDIA_PREVIEW_LIMIT) -> List[MessageMediaItem]:
    query = (
        db.query(MessageMedia)
        .filter(MessageMedia.message_id == message_id)
        .order_by(MessageMedia.position)
    )
    if limit is not None:
        query = query.limit(limit)
    relations = query.all()
    return [
        MessageMediaItem.model_validate(r.media)
        for r in relations
        if r.media
    ]


def _build_detail_response(db: Session, msg: Message, media_limit: Optional[int] = MEDIA_PREVIEW_LIMIT) -> MessageDetailResponse:
    media_items = _media_items_for(db, msg.id, limit=media_limit)
    tags = [MessageTagItem(id=t.id, name=t.name, category=t.category) for t in msg.tags]
    actor_name = msg.actor.name if msg.actor else None
    return MessageDetailResponse(
        id=msg.id,
        text=msg.text,
        actor_id=msg.actor_id,
        actor_name=actor_name,
        media_count=len(media_items),
        starred=bool(msg.starred),
        media_items=media_items,
        tags=tags,
        created_at=msg.created_at.isoformat(),
        updated_at=msg.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=CursorResponse)
def get_messages(
    cursor: Optional[str] = Query(None, description="游标，ISO 格式的 created_at"),
    limit: int = Query(20, ge=1, le=100),
    actor_id: Optional[int] = None,
    starred: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """获取消息列表（游标分页）"""
    cursor_time = _parse_cursor(cursor)
    query = _build_message_query(db, actor_id, None, None, None, cursor_time, starred=starred)
    items, has_more, next_cursor = _paginate(query, limit)

    # 批量查 media_count，避免 N+1
    ids = [m.id for m in items]
    counts = dict(
        db.query(MessageMedia.message_id, func.count())
        .filter(MessageMedia.message_id.in_(ids))
        .group_by(MessageMedia.message_id)
        .all()
    ) if ids else {}

    result = [
        MessageResponse(
            id=msg.id,
            text=msg.text,
            actor_id=msg.actor_id,
            actor_name=msg.actor.name if msg.actor else None,
            media_count=counts.get(msg.id, 0),
            starred=bool(msg.starred),
            created_at=msg.created_at.isoformat(),
            updated_at=msg.updated_at.isoformat(),
        )
        for msg in items
    ]
    return CursorResponse(items=result, next_cursor=next_cursor, has_more=has_more)


@router.get("/dates", response_model=MessageDatesResponse)
def get_message_dates(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    actor_id: Optional[int] = None,
    query_text: Optional[str] = Query(None),
    media_id: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """获取指定月份中有消息的日期及数量"""
    date_label = func.strftime('%Y-%m-%d', Message.created_at).label('date_str')
    query = db.query(date_label, func.count().label('cnt'))

    if actor_id:
        query = query.filter(Message.actor_id == actor_id)
    if query_text:
        query = query.filter(Message.text.ilike(f"%{query_text}%"))
    if media_id:
        query = query.join(MessageMedia, Message.id == MessageMedia.message_id).filter(MessageMedia.media_id == media_id)
    if tag_id:
        query = query.join(message_tag, Message.id == message_tag.c.message_id).filter(
            message_tag.c.tag_id == tag_id
        )

    query = query.filter(
        func.strftime('%Y', Message.created_at) == str(year),
        func.strftime('%m', Message.created_at) == str(month).zfill(2),
    )

    rows = query.group_by(date_label).all()
    dates = [MessageDateCount(date=row.date_str, count=row.cnt) for row in rows]
    return MessageDatesResponse(dates=dates)


@router.get("/sync", response_model=List[MessageSyncResponse])
def sync_messages(db: Session = Depends(get_db)):
    """全量同步：返回所有消息的完整详情（含 media 元数据和 tag）"""
    messages = db.query(Message).order_by(Message.created_at.desc()).all()
    results = []
    for msg in messages:
        relations = (
            db.query(MessageMedia)
            .filter(MessageMedia.message_id == msg.id)
            .order_by(MessageMedia.position)
            .all()
        )
        media_items = [
            MessageSyncMediaItem.model_validate(r.media, position=r.position)
            for r in relations
            if r.media
        ]
        tags = [MessageTagItem(id=t.id, name=t.name, category=t.category) for t in msg.tags]
        actor_name = msg.actor.name if msg.actor else None
        results.append(MessageSyncResponse(
            id=msg.id,
            text=msg.text,
            actor_id=msg.actor_id,
            actor_name=actor_name,
            starred=bool(msg.starred),
            created_at=msg.created_at.isoformat(),
            updated_at=msg.updated_at.isoformat(),
            media_items=media_items,
            tags=tags,
        ))
    return results


@router.get("/with-detail", response_model=MessageDetailCursorResponse)
def get_messages_with_detail(
    cursor: Optional[str] = Query(None, description="游标，ISO 格式的 created_at"),
    direction: Optional[str] = Query(None, description="分页方向: 'forward' 加载更新的消息（cursor 之后）"),
    limit: int = Query(20, ge=1, le=100),
    actor_id: Optional[int] = None,
    query_text: Optional[str] = Query(None, description="搜索文本，匹配 message.text"),
    media_id: Optional[int] = Query(None, description="媒体 ID，查询包含该媒体的所有消息"),
    tag_id: Optional[int] = Query(None, description="标签 ID，查询包含该标签的所有消息"),
    starred: Optional[bool] = Query(None, description="是否收藏"),
    db: Session = Depends(get_db),
):
    """获取消息列表，含完整媒体详情（游标分页）"""

    if direction == "forward" and cursor:
        pivot = _parse_cursor(cursor)
        op = Message.created_at > pivot
        query = _build_detail_query(db, actor_id, query_text, media_id, tag_id, starred)
        query = query.filter(op).order_by(Message.created_at.asc())
        rows = query.limit(limit + 1).all()
        has_more = len(rows) > limit
        items = rows[:limit]

        base = _build_detail_query(db, actor_id, query_text, media_id, tag_id, starred)
        has_more_before = base.filter(Message.created_at < pivot).first() is not None

        result = [_build_detail_response(db, msg) for msg in items]
        return MessageDetailCursorResponse(
            items=result,
            next_cursor=items[-1].created_at.isoformat() if has_more and items else None,
            prev_cursor=items[0].created_at.isoformat() if items else None,
            has_more=has_more,
            has_more_before=has_more_before,
        )

    # 默认：向后（desc）分页
    cursor_time = _parse_cursor(cursor)
    query = _build_message_query(db, actor_id, query_text, media_id, tag_id, cursor_time, starred=starred)
    items, has_more, next_cursor = _paginate(query, limit)

    result = [_build_detail_response(db, msg) for msg in items]
    return MessageDetailCursorResponse(items=result, next_cursor=next_cursor, has_more=has_more)


@router.get("/{message_id}", response_model=MessageDetailResponse)
def get_message_detail(
    message_id: int,
    db: Session = Depends(get_db),
):
    """获取单条消息详情"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return _build_detail_response(db, message, media_limit=None)


@router.post("", response_model=MessageDetailResponse, status_code=201)
def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
):
    """创建新消息"""
    db_message = Message(text=message_data.text, actor_id=message_data.actor_id)
    db.add(db_message)
    db.flush()

    sync_tags_from_text(db, db_message, message_data.text)

    position = 0
    for file_path in message_data.files:
        result = process_file(db, file_path, db_message.id, position)
        if result is not None:
            position += 1

    db.commit()
    db.refresh(db_message)
    return _build_detail_response(db, db_message)


@router.patch("/{message_id}", response_model=MessageDetailResponse)
def update_message(
    message_id: int,
    update_data: MessageUpdate,
    db: Session = Depends(get_db),
):
    """更新消息：文字、actor、媒体顺序"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if update_data.text is not None:
        message.text = update_data.text
        sync_tags_from_text(db, message, update_data.text)

    if update_data.actor_id is not None:
        message.actor_id = update_data.actor_id

    if update_data.starred is not None:
        message.starred = 1 if update_data.starred else 0

    if update_data.media_order is not None:
        if not reorder_message_media(db, message_id, update_data.media_order):
            raise HTTPException(status_code=422, detail="media_order 包含不属于该消息的 media_id")

    db.commit()
    db.refresh(message)
    return _build_detail_response(db, message)


@router.post("/merge", response_model=MessageDetailResponse)
def merge_messages(
    merge_data: MessageMerge,
    db: Session = Depends(get_db),
):
    """合并多条消息：文本拼接、媒体合并到第一条消息，删除其余消息。"""
    ids = merge_data.message_ids
    if len(ids) < 2:
        raise HTTPException(status_code=422, detail="至少需要两条消息才能合并")

    # 按 created_at 排序获取所有消息
    msgs = (
        db.query(Message)
        .filter(Message.id.in_(ids))
        .order_by(Message.created_at.asc())
        .all()
    )
    if len(msgs) != len(ids):
        raise HTTPException(status_code=404, detail="部分消息不存在")

    target = msgs[0]
    others = msgs[1:]

    # 合并文本
    texts = [m.text for m in msgs if m.text]
    if texts:
        target.text = "\n".join(texts)
        sync_tags_from_text(db, target, target.text)

    # 合并媒体：把其他消息的 media 接到 target 后面
    max_pos = (
        db.query(func.coalesce(func.max(MessageMedia.position), -1))
        .filter(MessageMedia.message_id == target.id)
        .scalar()
    )
    next_pos = max_pos + 1

    for other in others:
        relations = (
            db.query(MessageMedia)
            .filter(MessageMedia.message_id == other.id)
            .order_by(MessageMedia.position)
            .all()
        )
        for rel in relations:
            rel.message_id = target.id
            rel.position = next_pos
            next_pos += 1

    # 合并 tags（去重）
    all_tags = {t.id: t for t in target.tags}
    for other in others:
        for t in other.tags:
            all_tags[t.id] = t
    target.tags = list(all_tags.values())

    # 删除其余消息
    other_ids = [m.id for m in others]
    db.execute(message_tag.delete().where(message_tag.c.message_id.in_(other_ids)))
    db.query(Message).filter(Message.id.in_(other_ids)).delete(synchronize_session="fetch")

    db.commit()
    db.refresh(target)
    return _build_detail_response(db, target, media_limit=None)


@router.get("/around/{message_id}", response_model=MessageDetailCursorResponse)
def get_messages_around(
    message_id: int,
    limit: int = Query(20, ge=1, le=100),
    actor_id: Optional[int] = None,
    query_text: Optional[str] = Query(None),
    media_id: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None),
    starred: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """以指定消息为中心，向前/向后加载消息"""
    # 找到目标消息
    target = db.query(Message).filter(Message.id == message_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Message not found")

    half_limit = limit // 2

    # 构建基础查询（不含排序和游标）
    def build_base_query():
        query = db.query(Message)
        if actor_id:
            query = query.filter(Message.actor_id == actor_id)
        if query_text:
            query = query.filter(Message.text.ilike(f"%{query_text}%"))
        if media_id:
            query = query.join(MessageMedia).filter(MessageMedia.media_id == media_id)
        if tag_id:
            query = query.join(message_tag, Message.id == message_tag.c.message_id).filter(
                message_tag.c.tag_id == tag_id
            )
        if starred is not None:
            query = query.filter(Message.starred == (1 if starred else 0))
        return query

    # 向后加载：更旧的消息（created_at < target.created_at）
    older_query = build_base_query().filter(
        Message.created_at < target.created_at
    ).order_by(Message.created_at.desc())
    older = older_query.limit(half_limit + 1).all()
    has_more_older = len(older) > half_limit
    older = older[:half_limit]

    # 向前加载：更新的消息（created_at > target.created_at）
    newer_query = build_base_query().filter(
        Message.created_at > target.created_at
    ).order_by(Message.created_at.asc())
    newer = newer_query.limit(half_limit + 1).all()
    has_more_newer = len(newer) > half_limit
    newer = newer[:half_limit]

    # 合并结果：older(旧) + [target] + newer(新)
    # 按时间正序排列（旧 → 新），方便聊天界面展示
    messages = list(reversed(older)) + [target] + newer

    # 构建响应
    result = [_build_detail_response(db, msg, media_limit=None) for msg in messages]

    return MessageDetailCursorResponse(
        items=result,
        next_cursor=older[-1].created_at.isoformat() if has_more_older and older else None,
        prev_cursor=newer[-1].created_at.isoformat() if has_more_newer and newer else None,
        has_more=has_more_older,
        has_more_before=has_more_newer,
    )


@router.delete("/{message_id}", status_code=204)
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
):
    """删除消息"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.query(MessageMedia).filter(MessageMedia.message_id == message_id).delete()
    db.delete(message)
    db.commit()
