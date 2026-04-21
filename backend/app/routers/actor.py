from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import get_db, Actor, Message
from typing import List, Optional
from app.schemas.actor import ActorResponse, ActorSyncResponse, ActorListResponse
from app.config import config

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
            avatar=config.get_actor_avatar_url(a.id) if a.avatar_path else None,
        )
        for a in actors
    ]


@router.get("", response_model=ActorListResponse)
def get_actors(
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取演员列表（返回所有有消息的演员）"""
    query = db.query(Actor)

    if name:
        query = query.filter(Actor.name.ilike(f"%{name}%"))

    actors = query.all()

    no_actor_count = db.query(func.count(Message.id)).filter(Message.actor_id.is_(None)).scalar() or 0

    if not actors:
        return ActorListResponse(items=[], no_actor_count=no_actor_count)

    actor_ids = [a.id for a in actors]

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

    result.sort(key=lambda x: x.message_count, reverse=True)

    return ActorListResponse(items=result, no_actor_count=no_actor_count)


