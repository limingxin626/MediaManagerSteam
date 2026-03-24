from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Tagging, MediaTags
from app.services.media import MediaService
from app.services.tag import TagService


class MediaTagService:
    @staticmethod
    def get_tags_by_media(db: Session, media_id: int) -> List[Tagging]:
        return db.query(Tagging).join(MediaTags).filter(MediaTags.media_id == media_id).all()

    @staticmethod
    def add_tag(db: Session, media_id: int, tag_id: int) -> Optional[MediaTags]:
        if not MediaService.get_by_id(db, media_id) or not TagService.get_by_id(db, tag_id):
            return None

        existing = db.query(MediaTags).filter(
            MediaTags.media_id == media_id,
            MediaTags.tag_id == tag_id
        ).first()
        if existing:
            return None

        new_media_tag = MediaTags(media_id=media_id, tag_id=tag_id)
        db.add(new_media_tag)
        db.commit()
        db.refresh(new_media_tag)
        return new_media_tag

    @staticmethod
    def remove_tag(db: Session, media_id: int, tag_id: int) -> bool:
        if not MediaService.get_by_id(db, media_id) or not TagService.get_by_id(db, tag_id):
            return False

        db.query(MediaTags).filter(
            MediaTags.media_id == media_id,
            MediaTags.tag_id == tag_id
        ).delete()

        db.commit()
        return True
