from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import get_db, Message, MessageMedia, Tag, Media
from typing import List, Optional
from app.schemas.message import MessageCreate, MessageResponse, MessageDetailResponse, CursorResponse, MessageDetailCursorResponse
from app.utils import calculate_file_hash

router = APIRouter(prefix="/messages", tags=["messages"])

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

@router.get("/with-detail", response_model=MessageDetailCursorResponse)
def get_messages_with_detail(
    cursor: Optional[str] = Query(None, description="游标，格式为ISO格式的created_at时间"),
    limit: int = Query(20, ge=1, le=100),
    actor_id: Optional[int] = None,
    query_text: Optional[str] = Query(None, description="搜索文本，匹配message.text"),
    db: Session = Depends(get_db)
):
    """获取消息列表，包含完整的媒体详情（基于游标的分页）"""
    from datetime import datetime
    
    query = db.query(Message)
    
    if actor_id:
        query = query.filter(Message.actor_id == actor_id)
    
    if query_text:
        query = query.filter(Message.text.ilike(f"%{query_text}%"))
    
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
        
        tags = [{"id": t.id, "name": t.name, "category": t.category} for t in msg.tags]
        
        result.append(MessageDetailResponse(
            id=msg.id,
            text=msg.text,
            actor_id=msg.actor_id,
            actor_name=actor_name,
            media_count=len(media_items),
            media_items=media_items,
            tags=tags,
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
    
    tags = [{"id": t.id, "name": t.name, "category": t.category} for t in message.tags]
    
    return MessageDetailResponse(
        id=message.id,
        text=message.text,
        actor_id=message.actor_id,
        actor_name=actor_name,
        media_count=len(media_items),
        media_items=media_items,
        tags=tags,
        created_at=message.created_at.isoformat(),
        updated_at=message.updated_at.isoformat()
    )


@router.post("", response_model=MessageDetailResponse)
def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """创建新消息"""
    # 创建消息实例
    db_message = Message(
        text=message_data.text,
        actor_id=message_data.actor_id
    )
    db.add(db_message)
    db.flush()  # 获取 message.id 而不提交事务
    
    # 处理文件列表，创建 Media 实例并关联到 message
    media_items = []
    for i, file_path in enumerate(message_data.files):
        # 计算文件哈希值
        file_hash = calculate_file_hash(file_path)
        
        # 检查文件是否已存在（基于哈希值）
        existing_media = db.query(Media).filter(Media.file_hash == file_hash).first()
        if existing_media:
            media = existing_media
        else:
            # 创建新的 Media 实例
            media = Media(
                file_path=file_path,
                file_hash=file_hash
                # 其他字段可以根据实际情况添加
            )
            db.add(media)
            db.flush()  # 获取 media.id 而不提交事务
        
        # 创建 MessageMedia 关联
        message_media = MessageMedia(
            message_id=db_message.id,
            media_id=media.id,
            position=i
        )
        db.add(message_media)
        
        # 构建媒体项响应
        media_items.append({
            "id": media.id,
            "file_path": media.file_path,
            "mime_type": media.mime_type,
            "duration": media.duration
        })
    
    db.commit()
    db.refresh(db_message)
    
    # 获取 actor 名称
    actor_name = db_message.actor.name if db_message.actor else None
    
    return MessageDetailResponse(
        id=db_message.id,
        text=db_message.text,
        actor_id=db_message.actor_id,
        actor_name=actor_name,
        media_count=len(media_items),
        media_items=media_items,
        tags=[],  # 因为没有 tag_ids
        created_at=db_message.created_at.isoformat(),
        updated_at=db_message.updated_at.isoformat()
    )
