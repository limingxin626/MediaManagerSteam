from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import get_db, Media, Message, MessageMedia
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/media", tags=["media"])

class MediaResponse(BaseModel):
    id: int
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    rating: int
    view_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class MediaDetailResponse(MediaResponse):
    messages: List[dict]

class MediaCursorResponse(BaseModel):
    items: List[MediaResponse]
    next_cursor: Optional[str]
    has_more: bool

@router.get("", response_model=MediaCursorResponse)
def get_media(
    cursor: Optional[str] = Query(None, description="游标，格式为'created_at|position'"),
    limit: int = Query(20, ge=1, le=100),
    message_id: Optional[int] = None,
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
        
        # 如果提供了游标，解析并使用
        if cursor:
            try:
                parts = cursor.split('|')
                if len(parts) == 2:
                    cursor_time = datetime.fromisoformat(parts[0])
                    cursor_position = int(parts[1])
                    # 使用复合条件：created_at < cursor_time 或 (created_at = cursor_time AND position < cursor_position)
                    query = query.filter(
                        (MessageMedia.created_at < cursor_time) | 
                        ((MessageMedia.created_at == cursor_time) & (MessageMedia.position < cursor_position))
                    )
                else:
                    cursor_time = datetime.fromisoformat(cursor)
                    query = query.filter(MessageMedia.created_at < cursor_time)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid cursor format")
        
        # 按MessageMedia.created_at和position倒序排序
        query = query.order_by(MessageMedia.created_at.desc(), MessageMedia.position.desc())
        
        # 获取比请求多一条记录，用于判断是否有更多数据
        media_items = query.limit(limit + 1).all()
        
        has_more = len(media_items) > limit
        items = media_items[:limit]
        
        # 计算下一个游标
        next_cursor = None
        if has_more and items:
            # 获取最后一个media对应的MessageMedia信息
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
                view_count=item.view_count,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat()
            ))
        
        return MediaCursorResponse(
            items=result,
            next_cursor=next_cursor,
            has_more=has_more
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
        view_count=media.view_count,
        messages=messages,
        created_at=media.created_at.isoformat(),
        updated_at=media.updated_at.isoformat()
    )

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
