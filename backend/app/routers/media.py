from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import get_db, Media, MessageMedia
from typing import Optional
from app.schemas.media import MediaResponse, MediaDetailResponse, MediaCursorResponse

router = APIRouter(prefix="/media", tags=["media"])

@router.get("", response_model=MediaCursorResponse)
def get_media(
    cursor: Optional[str] = Query(None, description="游标，格式为'created_at|position'"),
    direction: Optional[str] = Query(None, description="分页方向: 'forward' 加载更新的媒体"),
    limit: int = Query(20, ge=1, le=100),
    message_id: Optional[int] = None,
    starred: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """获取媒体列表（基于MessageMedia的游标分页）"""
    from datetime import datetime
    
    if message_id:
        # 通过 message_id 获取媒体
        media_relations = db.query(MessageMedia).filter(
            MessageMedia.message_id == message_id
        ).order_by(MessageMedia.position).all()
        
        media_ids = [relation.media_id for relation in media_relations]
        media = db.query(Media).filter(Media.id.in_(media_ids)).all()
        
        # 对于固定message_id的情况，返回简单的列表
        result = []
        for item in media:
            result.append(MediaResponse(
                id=item.id,
                file_path=item.file_path,
                file_size=item.file_size,
                mime_type=item.mime_type,
                width=item.width,
                height=item.height,
                duration=item.duration,
                rating=item.rating,
                starred=bool(item.starred),
                view_count=item.view_count,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat()
            ))

        return MediaCursorResponse(
            items=result,
            next_cursor=None,
            has_more=False
        )
    else:
        # 基于MessageMedia的游标分页
        query = db.query(Media).join(MessageMedia)

        if starred is not None:
            query = query.filter(Media.starred == (1 if starred else 0))

        # 如果提供了游标，解析并使用
        if cursor:
            try:
                parts = cursor.split('|')
                if len(parts) == 2:
                    cursor_time = datetime.fromisoformat(parts[0])
                    cursor_position = int(parts[1])

                    if direction == 'forward':
                        # 向前加载：更新的媒体
                        query = query.filter(
                            (MessageMedia.created_at > cursor_time) |
                            ((MessageMedia.created_at == cursor_time) & (MessageMedia.position > cursor_position))
                        )
                        query = query.order_by(MessageMedia.created_at.asc(), MessageMedia.position.asc())
                    else:
                        # 向后加载：更旧的媒体
                        query = query.filter(
                            (MessageMedia.created_at < cursor_time) |
                            ((MessageMedia.created_at == cursor_time) & (MessageMedia.position < cursor_position))
                        )
                        query = query.order_by(MessageMedia.created_at.desc(), MessageMedia.position.desc())
                else:
                    cursor_time = datetime.fromisoformat(cursor)
                    if direction == 'forward':
                        query = query.filter(MessageMedia.created_at > cursor_time)
                        query = query.order_by(MessageMedia.created_at.asc(), MessageMedia.position.asc())
                    else:
                        query = query.filter(MessageMedia.created_at < cursor_time)
                        query = query.order_by(MessageMedia.created_at.desc(), MessageMedia.position.desc())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid cursor format")
        else:
            # 没有游标时，默认倒序（最新的在前）
            query = query.order_by(MessageMedia.created_at.desc(), MessageMedia.position.desc())

        # 获取比请求多一条记录，用于判断是否有更多数据
        media_items = query.limit(limit + 1).all()

        has_more = len(media_items) > limit
        items = media_items[:limit]

        # 计算游标
        next_cursor = None
        prev_cursor = None

        if has_more and items:
            if direction == 'forward':
                # 向前加载，最后一个是最新的，用它作为下一个游标
                last_media_id = items[-1].id
                last_mm = db.query(MessageMedia).filter(
                    MessageMedia.media_id == last_media_id
                ).order_by(MessageMedia.created_at.asc()).first()
                if last_mm:
                    next_cursor = f"{last_mm.created_at.isoformat()}|{last_mm.position}"
            else:
                # 向后加载，最后一个是最旧的，用它作为下一个游标
                last_media_id = items[-1].id
                last_mm = db.query(MessageMedia).filter(
                    MessageMedia.media_id == last_media_id
                ).order_by(MessageMedia.created_at.desc()).first()
                if last_mm:
                    next_cursor = f"{last_mm.created_at.isoformat()}|{last_mm.position}"

        # 构建响应
        result = []
        for item in items:
            result.append(MediaResponse(
                id=item.id,
                file_path=item.file_path,
                file_size=item.file_size,
                mime_type=item.mime_type,
                width=item.width,
                height=item.height,
                duration=item.duration,
                rating=item.rating,
                starred=bool(item.starred),
                view_count=item.view_count,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat()
            ))

        return MediaCursorResponse(
            items=result,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_more=has_more,
            has_more_before=False
        )

@router.get("/{media_id}", response_model=MediaDetailResponse)
def get_media_detail(
    media_id: int,
    db: Session = Depends(get_db)
):
    """获取媒体详情"""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # 获取媒体关联的消息
    media_relations = db.query(MessageMedia).filter(
        MessageMedia.media_id == media_id
    ).order_by(MessageMedia.created_at.desc()).all()
    
    messages = []
    for relation in media_relations:
        message = relation.message
        messages.append({
            "id": message.id,
            "text": message.text,
            "actor_id": message.actor_id,
            "actor_name": message.actor.name if message.actor else None,
            "position": relation.position,
            "created_at": message.created_at.isoformat()
        })
    
    return MediaDetailResponse(
        id=media.id,
        file_path=media.file_path,
        file_size=media.file_size,
        mime_type=media.mime_type,
        width=media.width,
        height=media.height,
        duration=media.duration,
        rating=media.rating,
        starred=bool(media.starred),
        view_count=media.view_count,
        messages=messages,
        created_at=media.created_at.isoformat(),
        updated_at=media.updated_at.isoformat()
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

@router.put("/{media_id}/view")
def increment_view_count(
    media_id: int,
    db: Session = Depends(get_db)
):
    """增加媒体查看次数"""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    media.view_count += 1
    media.last_viewed_at = db.func.current_timestamp()
    db.commit()

    return {"message": "View count updated", "view_count": media.view_count}


@router.get("/around/{media_id}", response_model=MediaCursorResponse)
def get_media_around(
    media_id: int,
    limit: int = Query(40, ge=1, le=100),
    starred: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """以指定媒体为中心，向前/向后加载媒体"""
    from datetime import datetime

    # 找到目标媒体对应的 MessageMedia 记录
    target_mm = db.query(MessageMedia).filter(
        MessageMedia.media_id == media_id
    ).order_by(MessageMedia.created_at.desc()).first()

    if not target_mm:
        raise HTTPException(status_code=404, detail="Media not found")

    half_limit = limit // 2

    # 构建基础查询
    def build_base_query():
        query = db.query(Media).join(MessageMedia)
        if starred is not None:
            query = query.filter(Media.starred == (1 if starred else 0))
        return query

    # 向后加载：更旧的媒体（created_at < target.created_at 或 created_at = target.created_at 且 position < target.position）
    older_query = build_base_query().filter(
        (MessageMedia.created_at < target_mm.created_at) |
        ((MessageMedia.created_at == target_mm.created_at) & (MessageMedia.position < target_mm.position))
    ).order_by(MessageMedia.created_at.desc(), MessageMedia.position.desc())
    older = older_query.limit(half_limit + 1).all()
    has_more_older = len(older) > half_limit
    older = older[:half_limit]

    # 向前加载：更新的媒体（created_at > target.created_at 或 created_at = target.created_at 且 position > target.position）
    newer_query = build_base_query().filter(
        (MessageMedia.created_at > target_mm.created_at) |
        ((MessageMedia.created_at == target_mm.created_at) & (MessageMedia.position > target_mm.position))
    ).order_by(MessageMedia.created_at.asc(), MessageMedia.position.asc())
    newer = newer_query.limit(half_limit + 1).all()
    has_more_newer = len(newer) > half_limit
    newer = newer[:half_limit]

    # 获取目标媒体
    target_media = db.query(Media).filter(Media.id == media_id).first()

    # 合并结果：older(旧) + [target] + newer(新)
    # 按时间正序排列（旧 → 新）
    media_items = list(reversed(older)) + [target_media] + newer

    # 构建响应
    result = []
    for item in media_items:
        result.append(MediaResponse(
            id=item.id,
            file_path=item.file_path,
            file_size=item.file_size,
            mime_type=item.mime_type,
            width=item.width,
            height=item.height,
            duration=item.duration,
            rating=item.rating,
            starred=bool(item.starred),
            view_count=item.view_count,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat()
        ))

    # 计算游标
    next_cursor = None
    if has_more_older and older:
        last_mm = db.query(MessageMedia).filter(
            MessageMedia.media_id == older[-1].id
        ).order_by(MessageMedia.created_at.desc()).first()
        if last_mm:
            next_cursor = f"{last_mm.created_at.isoformat()}|{last_mm.position}"

    prev_cursor = None
    if has_more_newer and newer:
        last_mm = db.query(MessageMedia).filter(
            MessageMedia.media_id == newer[-1].id
        ).order_by(MessageMedia.created_at.asc()).first()
        if last_mm:
            prev_cursor = f"{last_mm.created_at.isoformat()}|{last_mm.position}"

    return MediaCursorResponse(
        items=result,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
        has_more=has_more_older,
        has_more_before=has_more_newer,
    )
