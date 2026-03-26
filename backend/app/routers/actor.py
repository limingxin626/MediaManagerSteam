from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import get_db, Actor, Message, MessageMedia
from typing import List, Optional
from app.schemas.actor import ActorResponse, ActorDetailResponse

router = APIRouter(prefix="/actors", tags=["actors"])


@router.get("", response_model=List[ActorResponse])
def get_actors(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取演员列表"""
    query = db.query(Actor)

    if name:
        query = query.filter(Actor.name.ilike(f"%{name}%"))

    actors = query.order_by(Actor.name).offset(skip).limit(limit).all()

    result = []
    for actor in actors:
        message_count = db.query(Message).filter(Message.actor_id == actor.id).count()

        result.append(ActorResponse(
            id=actor.id,
            name=actor.name,
            description=actor.description,
            avatar_path=actor.avatar_path,
            message_count=message_count,
            created_at=actor.created_at.isoformat(),
            updated_at=actor.updated_at.isoformat()
        ))

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

    message_list = []
    for message in messages:
        media_count = db.query(MessageMedia).filter(MessageMedia.message_id == message.id).count()
        message_list.append({
            "id": message.id,
            "text": message.text,
            "media_count": media_count,
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
