from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import get_db, Actor, Message, MessageMedia
from typing import List, Optional
from app.schemas.actor import ActorResponse, ActorDetailResponse, ActorSyncResponse

router = APIRouter(prefix="/actors", tags=["actors"])


@router.get("/sync", response_model=List[ActorSyncResponse])
def sync_actors(db: Session = Depends(get_db)):
    """全量同步：返回所有演员（供 Android 拉取）"""
    actors = db.query(Actor).order_by(Actor.name).all()
    return [
        ActorSyncResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            avatar=f"/asktao/data/actor_cover/{a.id}.webp" if a.avatar_path else None,
        )
        for a in actors
    ]


@router.get("", response_model=List[ActorResponse])
def get_actors(
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取演员列表（返回所有有消息的演员）"""
    query = db.query(Actor)

    if name:
        query = query.filter(Actor.name.ilike(f"%{name}%"))

    actors = query.all()
    if not actors:
        return []

    actor_ids = [a.id for a in actors]

    # 批量获取各演员的消息数，避免 N+1
    counts = (
        db.query(Message.actor_id, func.count(Message.id).label("cnt"))
        .filter(Message.actor_id.in_(actor_ids))
        .group_by(Message.actor_id)
        .all()
    )
    count_map = {row.actor_id: row.cnt for row in counts}

    result = []
    for actor in actors:
        message_count = count_map.get(actor.id, 0)
        if message_count > 0:
            result.append(ActorResponse(
                id=actor.id,
                name=actor.name,
                description=actor.description,
                avatar_path=actor.avatar_path,
                message_count=message_count,
                created_at=actor.created_at.isoformat(),
                updated_at=actor.updated_at.isoformat()
            ))

    # 按消息数量倒序排列
    result.sort(key=lambda x: x.message_count, reverse=True)

    return result


@router.get("/{actor_id}", response_model=ActorDetailResponse)
def get_actor_detail(
    actor_id: int,
    db: Session = Depends(get_db)
):
    """获取演员详情"""
    actor = db.query(Actor).filter(Actor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    messages = db.query(Message).filter(
        Message.actor_id == actor_id
    ).order_by(Message.created_at.desc()).all()

    if messages:
        message_ids = [m.id for m in messages]
        # 批量获取各消息的媒体数，避免 N+1
        media_counts = (
            db.query(MessageMedia.message_id, func.count(MessageMedia.id).label("cnt"))
            .filter(MessageMedia.message_id.in_(message_ids))
            .group_by(MessageMedia.message_id)
            .all()
        )
        media_count_map = {row.message_id: row.cnt for row in media_counts}
    else:
        media_count_map = {}

    message_list = []
    for message in messages:
        message_list.append({
            "id": message.id,
            "text": message.text,
            "media_count": media_count_map.get(message.id, 0),
            "created_at": message.created_at.isoformat()
        })

    return ActorDetailResponse(
        id=actor.id,
        name=actor.name,
        description=actor.description,
        avatar_path=actor.avatar_path,
        message_count=len(message_list),
        messages=message_list,
        created_at=actor.created_at.isoformat(),
        updated_at=actor.updated_at.isoformat()
    )
