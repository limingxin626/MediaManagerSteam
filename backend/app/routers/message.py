from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import get_db, Message, MessageMedia
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/messages", tags=["messages"])

class MessageResponse(BaseModel):
    id: int
    text: Optional[str]
    actor_id: Optional[int]
    actor_name: Optional[str]
    media_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class MessageDetailResponse(MessageResponse):
    media_items: List[dict]

class CursorResponse(BaseModel):
    items: List[MessageResponse]
    next_cursor: Optional[str]
    has_more: bool

@router.get("", response_model=CursorResponse)
def get_messages(
    cursor: Optional[str] = Query(None, description="游标，格式为ISO格式的created_at时间"),
    limit: int = Query(20, ge=1, le=100),
    actor_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取消息列表（基于游标的分页）"""
    from datetime import datetime
    
    query = db.query(Message)
    
    if actor_id:
        query = query.filter(Message.actor_id == actor_id)
    
    # 如果提供了游标，解析并使用
    if cursor:
        try:
            cursor_time = datetime.fromisoformat(cursor)
            query = query.filter(Message.created_at < cursor_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor format")
    
    # 按时间倒序排序
    query = query.order_by(Message.created_at.desc())
    
    # 获取比请求多一条记录，用于判断是否有更多数据
    messages = query.limit(limit + 1).all()
    
    has_more = len(messages) > limit
    items = messages[:limit]
    
    # 计算下一个游标
    next_cursor = None
    if has_more and items:
        next_cursor = items[-1].created_at.isoformat()
    
    # 构建响应
    result = []
    for msg in items:
        media_count = db.query(MessageMedia).filter(MessageMedia.message_id == msg.id).count()
        actor_name = msg.actor.name if msg.actor else None
        
        result.append(MessageResponse(
            id=msg.id,
            text=msg.text,
            actor_id=msg.actor_id,
            actor_name=actor_name,
            media_count=media_count,
            created_at=msg.created_at.isoformat(),
            updated_at=msg.updated_at.isoformat()
        ))
    
    return CursorResponse(
        items=result,
        next_cursor=next_cursor,
        has_more=has_more
    )

class MessageDetailCursorResponse(BaseModel):
    items: List[MessageDetailResponse]
    next_cursor: Optional[str]
    has_more: bool

@router.get("/with-detail", response_model=MessageDetailCursorResponse)
def get_messages_with_detail(
    cursor: Optional[str] = Query(None, description="游标，格式为ISO格式的created_at时间"),
    limit: int = Query(20, ge=1, le=100),
    actor_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取消息列表，包含完整的媒体详情（基于游标的分页）"""
    from datetime import datetime
    
    query = db.query(Message)
    
    if actor_id:
        query = query.filter(Message.actor_id == actor_id)
    
    # 如果提供了游标，解析并使用
    if cursor:
        try:
            cursor_time = datetime.fromisoformat(cursor)
            query = query.filter(Message.created_at < cursor_time)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor format")
    
    # 按时间倒序排序
    query = query.order_by(Message.created_at.desc())
    
    # 获取比请求多一条记录，用于判断是否有更多数据
    messages = query.limit(limit + 1).all()
    
    has_more = len(messages) > limit
    items = messages[:limit]
    
    # 计算下一个游标
    next_cursor = None
    if has_more and items:
        next_cursor = items[-1].created_at.isoformat()
    
    # 构建响应
    result = []
    for msg in items:
        media_relations = db.query(MessageMedia).filter(
            MessageMedia.message_id == msg.id
        ).order_by(MessageMedia.position).limit(9).all()
        
        media_items = []
        for relation in media_relations:
            media = relation.media
            if media:
                media_items.append({
                    "id": media.id,
                    "file_path": media.file_path,
                    "mime_type": media.mime_type,
                    "duration": media.duration
                })
        
        actor_name = msg.actor.name if msg.actor else None
        
        result.append(MessageDetailResponse(
            id=msg.id,
            text=msg.text,
            actor_id=msg.actor_id,
            actor_name=actor_name,
            media_count=len(media_items),
            media_items=media_items,
            created_at=msg.created_at.isoformat(),
            updated_at=msg.updated_at.isoformat()
        ))
    
    return MessageDetailCursorResponse(
        items=result,
        next_cursor=next_cursor,
        has_more=has_more
    )

@router.get("/{message_id}", response_model=MessageDetailResponse)
def get_message_detail(
    message_id: int,
    db: Session = Depends(get_db)
):
    """获取消息详情"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    media_relations = db.query(MessageMedia).filter(
        MessageMedia.message_id == message_id
    ).order_by(MessageMedia.position).limit(9).all()
    
    media_items = []
    for relation in media_relations:
        media = relation.media
        if media:
            media_items.append({
                "id": media.id,
                "file_path": media.file_path,
                "mime_type": media.mime_type,
                "duration": media.duration
            })
    
    actor_name = message.actor.name if message.actor else None
    
    return MessageDetailResponse(
        id=message.id,
        text=message.text,
        actor_id=message.actor_id,
        actor_name=actor_name,
        media_count=len(media_items),
        media_items=media_items,
        created_at=message.created_at.isoformat(),
        updated_at=message.updated_at.isoformat()
    )
