import os
import logging
import mimetypes
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Media, MessageMedia
from app.utils import calculate_file_hash, ThumbnailUtils, MediaInfoUtils
from app.config import config

logger = logging.getLogger(__name__)


def process_file(db: Session, file_path: str, message_id: int, position: int) -> Optional[Dict[str, Any]]:
    """
    处理单个文件：hash 去重 → 媒体信息提取 → 缩略图生成 → 创建 MessageMedia。
    返回 {"media": Media, "is_new": bool} 或 None（文件不存在或不支持的类型）。
    """
    if not os.path.exists(file_path):
        return None

    media_type = config.get_media_type(file_path)
    if media_type is None:
        logger.warning(f"Unsupported media type, skipping: {file_path}")
        return None

    file_hash = calculate_file_hash(file_path)
    if file_hash is None:
        logger.error(f"Failed to calculate hash, skipping: {file_path}")
        return None

    existing_media = db.query(Media).filter(Media.file_hash == file_hash).first()
    if existing_media:
        _link_media(db, message_id, existing_media.id, position)
        return {"media": existing_media, "is_new": False}

    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    media_info = MediaInfoUtils.get_media_info(file_path, media_type, config.FFPROBE_PATH)

    media = Media(
        file_path=file_path,
        file_hash=file_hash,
        file_size=file_size,
        mime_type=mime_type or 'application/octet-stream',
        width=media_info["width"],
        height=media_info["height"],
        duration=media_info["duration"],
    )
    db.add(media)
    db.flush()

    try:
        thumb_path = config.get_thumbnail_path(media.id)
        ThumbnailUtils.generate_thumbnail(file_path, thumb_path, media_type, config.FFMPEG_PATH)
    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}")

    _link_media(db, message_id, media.id, position)
    return {"media": media, "is_new": True}


def _link_media(db: Session, message_id: int, media_id: int, position: int) -> None:
    mm = MessageMedia(message_id=message_id, media_id=media_id, position=position)
    db.add(mm)
