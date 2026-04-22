from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import get_db, Tag, message_tag, media_tag, MessageMedia
from app.schemas.tag import TagResponse, TagCreate, TagUpdate
from typing import List, Optional

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=List[TagResponse])
def get_tags(
    name: Optional[str] = Query(None, description="按名称模糊搜索"),
    has_media: bool = Query(False, description="只返回关联了媒体的标签"),
    db: Session = Depends(get_db)
):
    """获取所有标签，支持按名称搜索，附带每个标签的关联数量。"""
    if has_media:
        msg_media_count_sub = (
            db.query(message_tag.c.tag_id, func.count(func.distinct(MessageMedia.media_id)).label("cnt"))
            .join(MessageMedia, MessageMedia.message_id == message_tag.c.message_id)
            .group_by(message_tag.c.tag_id)
            .subquery()
        )
        direct_media_count_sub = (
            db.query(media_tag.c.tag_id, func.count().label("cnt"))
            .group_by(media_tag.c.tag_id)
            .subquery()
        )
        total = (func.coalesce(msg_media_count_sub.c.cnt, 0) + func.coalesce(direct_media_count_sub.c.cnt, 0)).label("message_count")
        query = (
            db.query(Tag, total)
            .outerjoin(msg_media_count_sub, Tag.id == msg_media_count_sub.c.tag_id)
            .outerjoin(direct_media_count_sub, Tag.id == direct_media_count_sub.c.tag_id)
        )
    else:
        msg_count_sub = (
            db.query(message_tag.c.tag_id, func.count().label("cnt"))
            .group_by(message_tag.c.tag_id)
            .subquery()
        )
        media_count_sub = (
            db.query(media_tag.c.tag_id, func.count().label("cnt"))
            .group_by(media_tag.c.tag_id)
            .subquery()
        )
        total = (func.coalesce(msg_count_sub.c.cnt, 0) + func.coalesce(media_count_sub.c.cnt, 0)).label("message_count")
        query = (
            db.query(Tag, total)
            .outerjoin(msg_count_sub, Tag.id == msg_count_sub.c.tag_id)
            .outerjoin(media_count_sub, Tag.id == media_count_sub.c.tag_id)
        )

    if name:
        query = query.filter(Tag.name.ilike(f"%{name}%"))

    if has_media:
        query = query.filter(total > 0)

    query = query.order_by(total.desc())

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


@router.post("", response_model=TagResponse, status_code=201)
def create_tag(
    data: TagCreate,
    db: Session = Depends(get_db),
):
    """创建新标签"""
    existing = db.query(Tag).filter(Tag.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="标签名已存在")
    tag = Tag(name=data.name, category=data.category)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    count = db.query(func.count()).select_from(message_tag).filter(message_tag.c.tag_id == tag.id).scalar()
    return TagResponse(id=tag.id, name=tag.name, category=tag.category, message_count=count)


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: int,
    data: TagUpdate,
    db: Session = Depends(get_db),
):
    """重命名/修改标签分类"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if data.name is not None:
        dup = db.query(Tag).filter(Tag.name == data.name, Tag.id != tag_id).first()
        if dup:
            raise HTTPException(status_code=409, detail="标签名已存在")
        tag.name = data.name
    if data.category is not None:
        tag.category = data.category
    db.commit()
    db.refresh(tag)
    count = db.query(func.count()).select_from(message_tag).filter(message_tag.c.tag_id == tag.id).scalar()
    return TagResponse(id=tag.id, name=tag.name, category=tag.category, message_count=count)


@router.delete("/{tag_id}", status_code=204)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
):
    """删除标签及其关联"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.execute(message_tag.delete().where(message_tag.c.tag_id == tag_id))
    db.execute(media_tag.delete().where(media_tag.c.tag_id == tag_id))
    db.delete(tag)
    db.commit()
