from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import get_db, Collection, Message
from typing import List, Optional
from app.schemas.collection import (
    CollectionResponse, CollectionSyncResponse, CollectionListResponse,
    CollectionCreate, CollectionUpdate,
)
from app.config import config

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/sync", response_model=List[CollectionSyncResponse])
def sync_collections(db: Session = Depends(get_db)):
    """全量同步：返回所有合集（供 Android 拉取）"""
    collections = db.query(Collection).order_by(Collection.name).all()
    return [
        CollectionSyncResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            cover=config.get_collection_cover_url(c.id) if c.cover_path else None,
        )
        for c in collections
    ]


@router.get("", response_model=CollectionListResponse)
def get_collections(
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取合集列表（返回所有有消息的合集）"""
    query = db.query(Collection)

    if name:
        query = query.filter(Collection.name.ilike(f"%{name}%"))

    collections = query.all()

    no_collection_count = db.query(func.count(Message.id)).filter(Message.collection_id.is_(None)).scalar() or 0

    if not collections:
        return CollectionListResponse(items=[], no_collection_count=no_collection_count)

    collection_ids = [c.id for c in collections]

    counts = (
        db.query(Message.collection_id, func.count(Message.id).label("cnt"))
        .filter(Message.collection_id.in_(collection_ids))
        .group_by(Message.collection_id)
        .all()
    )
    count_map = {row.collection_id: row.cnt for row in counts}

    result = []
    for collection in collections:
        message_count = count_map.get(collection.id, 0)
        if message_count > 0:
            result.append(CollectionResponse(
                id=collection.id,
                name=collection.name,
                description=collection.description,
                cover_path=collection.cover_path,
                message_count=message_count,
                created_at=collection.created_at.isoformat(),
                updated_at=collection.updated_at.isoformat()
            ))

    result.sort(key=lambda x: x.message_count, reverse=True)

    return CollectionListResponse(items=result, no_collection_count=no_collection_count)


@router.post("", response_model=CollectionResponse, status_code=201)
def create_collection(
    data: CollectionCreate,
    db: Session = Depends(get_db),
):
    """新建合集（名称唯一）"""
    existing = db.query(Collection).filter(Collection.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="合集名已存在")
    collection = Collection(name=data.name, description=data.description)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        cover_path=collection.cover_path,
        message_count=0,
        created_at=collection.created_at.isoformat(),
        updated_at=collection.updated_at.isoformat(),
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: int,
    data: CollectionUpdate,
    db: Session = Depends(get_db),
):
    """重命名 / 修改合集描述"""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if data.name is not None:
        dup = db.query(Collection).filter(Collection.name == data.name, Collection.id != collection_id).first()
        if dup:
            raise HTTPException(status_code=409, detail="合集名已存在")
        collection.name = data.name
    if data.description is not None:
        collection.description = data.description
    db.commit()
    db.refresh(collection)
    message_count = db.query(func.count(Message.id)).filter(Message.collection_id == collection_id).scalar() or 0
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        cover_path=collection.cover_path,
        message_count=message_count,
        created_at=collection.created_at.isoformat(),
        updated_at=collection.updated_at.isoformat(),
    )


@router.delete("/{collection_id}", status_code=204)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
):
    """删除合集：其下 message 的 collection_id 置 NULL，不级联删 message"""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    db.query(Message).filter(Message.collection_id == collection_id).update(
        {Message.collection_id: None}, synchronize_session=False
    )
    db.delete(collection)
    db.commit()
