from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import get_db, Media, MessageMedia, Message, message_tag
from typing import Optional
from app.schemas.media import MediaResponse, MediaCursorResponse

router = APIRouter(prefix="/media", tags=["media"])

@router.get("", response_model=MediaCursorResponse)
def get_media(
    cursor: Optional[str] = Query(None, description="游标，格式为'created_at|position'"),
    direction: Optional[str] = Query(None, description="分页方向: 'forward' 加载更新的媒体"),
    limit: int = Query(20, ge=1, le=100),
    message_id: Optional[int] = None,
    starred: Optional[bool] = Query(None),
    type: Optional[str] = Query(None, description="媒体类型: 'video' 或 'image'"),
    db: Session = Depends(get_db)
):
    """获取媒体列表（游标分页，显示所有媒体）"""

    if message_id:
        # 通过 message_id 获取媒体
        media_relations = db.query(MessageMedia).filter(
            MessageMedia.message_id == message_id
        ).order_by(MessageMedia.position).all()
        
        media_ids = [relation.media_id for relation in media_relations]
        media = db.query(Media).filter(Media.id.in_(media_ids)).all()
        
        # 对于固定message_id的情况，返回简单的列表
        result = [MediaResponse.model_validate(item) for item in media]

        return MediaCursorResponse(
            items=result,
            next_cursor=None,
            has_more=False
        )
    else:
        # 直接查 Media 表，显示所有媒体（包括孤立媒体）
        query = db.query(Media)

        if starred is not None:
            query = query.filter(Media.starred == (1 if starred else 0))
        
        if type == 'video':
            query = query.filter(Media.mime_type.like('video/%'))
        elif type == 'image':
            query = query.filter(Media.mime_type.like('image/%'))

        # 游标格式："{created_at}|{id}"
        if cursor:
            try:
                parts = cursor.split('|')
                cursor_time = datetime.fromisoformat(parts[0])
                cursor_id = int(parts[1])

                if direction == 'forward':
                    query = query.filter(
                        (Media.created_at > cursor_time) |
                        ((Media.created_at == cursor_time) & (Media.id > cursor_id))
                    )
                    query = query.order_by(Media.created_at.asc(), Media.id.asc())
                else:
                    query = query.filter(
                        (Media.created_at < cursor_time) |
                        ((Media.created_at == cursor_time) & (Media.id < cursor_id))
                    )
                    query = query.order_by(Media.created_at.desc(), Media.id.desc())
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid cursor format")
        else:
            query = query.order_by(Media.created_at.desc(), Media.id.desc())

        media_items = query.limit(limit + 1).all()

        has_more = len(media_items) > limit
        items = media_items[:limit]

        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = f"{last.created_at.isoformat()}|{last.id}"

        result = [MediaResponse.model_validate(item) for item in items]

        return MediaCursorResponse(
            items=result,
            next_cursor=next_cursor,
            prev_cursor=None,
            has_more=has_more,
            has_more_before=False
        )

@router.get("/feed", response_model=MediaCursorResponse)
def get_media_feed(
    cursor: Optional[int] = Query(None, description="游标：message_media.id"),
    limit: int = Query(40, ge=1, le=100),
    tag_id: Optional[int] = Query(None),
    actor_id: Optional[int] = Query(None),
    starred: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """按 MessageMedia 展开的媒体流（Telegram风格，媒体可重复），支持 tag/actor 筛选"""
    query = (
        db.query(Media, MessageMedia)
        .join(MessageMedia, MessageMedia.media_id == Media.id)
        .join(Message, Message.id == MessageMedia.message_id)
    )

    if tag_id is not None:
        query = query.filter(
            Message.id.in_(
                db.query(message_tag.c.message_id).filter(message_tag.c.tag_id == tag_id)
            )
        )

    if actor_id is not None:
        query = query.filter(Message.actor_id == actor_id)

    if starred is not None:
        query = query.filter(Media.starred == (1 if starred else 0))

    if cursor is not None:
        query = query.filter(MessageMedia.id < cursor)

    query = query.order_by(MessageMedia.id.desc())

    rows = query.limit(limit + 1).all()

    has_more = len(rows) > limit
    rows = rows[:limit]

    next_cursor = str(rows[-1][1].id) if has_more and rows else None

    result = [MediaResponse.model_validate(media) for media, _ in rows]

    return MediaCursorResponse(
        items=result,
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.put("/{media_id}/starred")
def toggle_media_starred(
    media_id: int,
    starred: bool = Query(...),
    db: Session = Depends(get_db)
):
    """切换媒体收藏状态"""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    media.starred = 1 if starred else 0
    db.commit()

    return {"starred": starred}

@router.put("/{media_id}/rating")
def update_media_rating(
    media_id: int,
    rating: int = Query(..., ge=0, le=10),
    db: Session = Depends(get_db)
):
    """更新媒体评分"""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    media.rating = rating
    db.commit()
    
    return {"message": "Rating updated successfully", "rating": rating}

