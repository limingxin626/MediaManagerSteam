from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Tagging, ActorTags, MediaTags


class TagService:
    # 内存缓存
    _tags_cache: Optional[List[Tagging]] = None
    
    @staticmethod
    def get_all(db: Session) -> List[Tagging]:
        # 如果缓存存在，直接返回缓存数据
        if TagService._tags_cache is not None:
            return TagService._tags_cache
        
        # 缓存不存在，从数据库查询并缓存
        tags = db.query(Tagging).all()
        TagService._tags_cache = tags
        return tags
    
    @staticmethod
    def _clear_cache():
        """清除缓存，在数据变更时调用"""
        TagService._tags_cache = None

    @staticmethod
    def get_by_id(db: Session, tag_id: int) -> Optional[Tagging]:
        return db.query(Tagging).filter(Tagging.id == tag_id).first()

    @staticmethod
    def get_by_category(db: Session, tag_category: str) -> List[Tagging]:
        return db.query(Tagging).filter(Tagging.category == tag_category).all()

    @staticmethod
    def get_by_actor_id(db: Session, actor_id: int) -> List[Tagging]:
        return db.query(Tagging).join(ActorTags).filter(ActorTags.actor_id == actor_id).all()

    @staticmethod
    def get_by_media_id(db: Session, media_id: int) -> List[Tagging]:
        return db.query(Tagging).join(MediaTags).filter(MediaTags.media_id == media_id).all()

    @staticmethod
    def create(db: Session, tag_data: Dict[str, Any]) -> Tagging:
        db_tag = Tagging(**tag_data)
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        # 清除缓存
        TagService._clear_cache()
        return db_tag

    @staticmethod
    def update(db: Session, tag_id: int, tag_data: Dict[str, Any]) -> Optional[Tagging]:
        db_tag = db.query(Tagging).filter(Tagging.id == tag_id).first()
        if not db_tag:
            return None

        for key, value in tag_data.items():
            setattr(db_tag, key, value)

        db.commit()
        db.refresh(db_tag)
        # 清除缓存
        TagService._clear_cache()
        return db_tag

    @staticmethod
    def delete(db: Session, tag_id: int) -> bool:
        db_tag = db.query(Tagging).filter(Tagging.id == tag_id).first()
        if not db_tag:
            return False

        db.delete(db_tag)
        db.commit()
        # 清除缓存
        TagService._clear_cache()
        return True
