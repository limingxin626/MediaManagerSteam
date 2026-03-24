from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Media, get_db
from app.services.media import MediaService


class LegacyService:
    @staticmethod
    def get_db() -> Session:
        return next(get_db())

    @staticmethod
    def media_to_dict(media: Media) -> Dict[str, Any]:
        return {
            "id": media.id,
            "name": media.name,
            "type": media.type.value,
            "description": media.description,
            "group_id": media.group_id,
            "created_at": media.created_at.strftime("%Y-%m-%d"),
            "local_media_path": media.local_media_path
        }

    @staticmethod
    def get_all_media() -> List[Dict[str, Any]]:
        db = LegacyService.get_db()
        media_list = MediaService.get_all(db)
        return [LegacyService.media_to_dict(m) for m in media_list]

    @staticmethod
    def get_media_by_id(media_id: int) -> Optional[Dict[str, Any]]:
        db = LegacyService.get_db()
        media = MediaService.get_by_id(db, media_id)
        if not media:
            return None
        return LegacyService.media_to_dict(media)
