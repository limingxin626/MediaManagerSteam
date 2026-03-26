from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import get_db, Tag, message_tag
from app.schemas.tag import TagResponse
from typing import List, Optional

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=List[TagResponse])
def get_tags(
    name: Optional[str] = Query(None, description="按名称模糊搜索"),
    db: Session = Depends(get_db)
):
    """获取所有标签，支持按名称搜索，附带每个标签的消息数量。"""
    query = db.query(
        Tag,
        func.count(message_tag.c.message_id).label("message_count")
    ).outerjoin(message_tag, Tag.id == message_tag.c.tag_id).group_by(Tag.id)

    if name:
        query = query.filter(Tag.name.ilike(f"%{name}%"))

    query = query.order_by(func.count(message_tag.c.message_id).desc())

    results = query.all()
    return [
        TagResponse(
            id=tag.id,
            name=tag.name,
            category=tag.category,
            message_count=count
        )
        for tag, count in results
    ]
