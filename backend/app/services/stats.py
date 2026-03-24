from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Actor, Group, Media, Tagging


class StatsService:
    @staticmethod
    def get_stats(db: Session) -> Dict[str, int]:
        return {
            "total_actors": db.query(func.count(Actor.id)).scalar(),
            "total_groups": db.query(func.count(Group.id)).scalar(),
            "total_media": db.query(func.count(Media.id)).scalar(),
            "total_tags": db.query(func.count(Tagging.id)).scalar()
        }
