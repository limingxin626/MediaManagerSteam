from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload, contains_eager
from sqlalchemy import func
from app.models import Media, Group, MediaTags, Actor, MediaType
from app.config import config
from app.schemas import MediaDetail
from app.utils import calculate_file_hash, ThumbnailUtils
import datetime


class MediaService:
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Media]:
        return db.query(Media).offset(skip).limit(limit).all()

    @staticmethod
    def search(db: Session, filters: Dict[str, Any] = None, skip: int = 0, limit: int = 100,
              sort_by: str = "id", sort_order: str = "asc") -> List[Media]:
        query = db.query(Media)

        if filters:
            if "type" in filters and filters["type"]:
                query = query.filter(Media.type == filters["type"])

            if "name" in filters and filters["name"]:
                query = query.filter(Media.name.like(f"%{filters['name']}%"))

        valid_sort_fields = ["id", "name", "file_size", "view_count", "rating", "date", "duration"]
        if sort_by not in valid_sort_fields:
            sort_by = "rating"

        sort_column = getattr(Media, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def search_count(db: Session, filters: Dict[str, Any] = None) -> int:
        query = db.query(func.count(Media.id))

        if filters:
            if "type" in filters and filters["type"]:
                query = query.filter(Media.type == filters["type"])

            if "name" in filters and filters["name"]:
                query = query.filter(Media.name.like(f"%{filters['name']}%"))

        return query.scalar()

    @staticmethod
    def get_total_count(db: Session) -> int:
        return db.query(func.count(Media.id)).scalar()

    @staticmethod
    def get_by_id(db: Session, media_id: int) -> Optional[Media]:
        return db.query(Media).filter(Media.id == media_id).first()

    @staticmethod
    def get_detail(db: Session, media_id: int) -> Optional[MediaDetail]:
        # 使用joinedload一次性加载关联的actor、group、tags和子媒体(previews)信息
        # previews会按照start_time自动排序（在模型中定义）
        return db.query(Media).options(
            joinedload(Media.actor),
            joinedload(Media.group),
            joinedload(Media.tags),
            joinedload(Media.previews)
        ).filter(Media.id == media_id).first()

    @staticmethod
    def create(db: Session, media_data: Dict[str, Any]) -> Optional[Media]:
        group = db.query(Group).filter(Group.id == media_data["group_id"]).first()
        if not group:
            return None

        media_data["created_at"] = datetime.datetime.now()
        media_data["updated_at"] = datetime.datetime.now()

        db_media = Media(**media_data)
        db.add(db_media)
        db.commit()
        db.refresh(db_media)
        return db_media

    @staticmethod
    def update(db: Session, media_id: int, update_data: Dict[str, Any]) -> Optional[Media]:
        db_media = db.query(Media).filter(Media.id == media_id).first()
        if not db_media:
            return None

        if "group_id" in update_data:
            group = db.query(Group).filter(Group.id == update_data["group_id"]).first()
            if not group:
                return None

        update_data["updated_at"] = datetime.datetime.now()

        for key, value in update_data.items():
            setattr(db_media, key, value)

        db.commit()
        db.refresh(db_media)
        return db_media

    @staticmethod
    def delete(db: Session, media_id: int) -> bool:
        db_media = db.query(Media).filter(Media.id == media_id).first()
        if not db_media:
            return False

        db.query(MediaTags).filter(MediaTags.media_id == media_id).delete()

        db.delete(db_media)
        db.commit()
        return True

    @staticmethod
    def create_with_file(db: Session, media_data: Dict[str, Any], file_path: str) -> Optional[Media]:
        group = db.query(Group).filter(Group.id == media_data["group_id"]).first()
        if not group:
            return None

        media_data["created_at"] = datetime.datetime.now()
        media_data["updated_at"] = datetime.datetime.now()
        media_data["local_media_path"] = file_path

        db_media = Media(**media_data)
        db.add(db_media)
        db.commit()
        db.refresh(db_media)

        db_media.remote_media_url = f"/api/media/file/{db_media.id}"
        db.commit()
        db.refresh(db_media)

        return db_media

    @staticmethod
    def get_by_type(db: Session, media_type: MediaType) -> List[Media]:
        return db.query(Media).filter(Media.type == media_type).all()

    @staticmethod
    def get_by_actor(db: Session, actor_id: int) -> List[Media]:
        return db.query(Media).filter(Media.actor_id == actor_id).order_by(Media.group_id, Media.name).all()

    @staticmethod
    def get_by_group(db: Session, group_id: int, sort_by: str = "name", sort_order: str = "asc") -> List[Media]:
        query = db.query(Media).filter(Media.group_id == group_id)

        sort_column = getattr(Media, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        return query.all()

    @staticmethod
    def add_media_from_file(db: Session, file_path: str, group_id: int, actor_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        从文件添加媒体到数据库
        
        Returns:
            Dict with keys:
                - media: Media对象
                - is_new: 是否为新创建的媒体
            或 None（如果失败）
        """
        try:
            import os
            import hashlib
            import logging
            
            logger = logging.getLogger(__name__)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return None
            
            # 检查文件类型（使用统一配置）
            media_type = config.get_media_type(file_path)
            if not media_type:
                return None
            
            # 获取文件名（不带扩展名）
            file_name_with_ext = os.path.basename(file_path)
            file_name = os.path.splitext(file_name_with_ext)[0]
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 初始化媒体属性
            height = None
            width = None
            ratio = None
            duration = None
            file_hash = None
            
            # 获取文件哈希值
            file_hash = calculate_file_hash(file_path)
            
            # 检查是否已存在相同hash的媒体（在同一个group中）
            if file_hash:
                existing_media = db.query(Media).filter(
                    Media.group_id == group_id,
                    Media.file_hash == file_hash,
                ).first()
                
                if existing_media:
                    return {"media": existing_media, "is_new": False}
            
            # 获取媒体属性
            if media_type == "VIDEO":
                # 使用ffprobe获取视频属性
                try:
                    import subprocess
                    import json
                    import sys
                    ffprobe = config.FFPROBE_PATH
                    
                    # 在Windows上处理编码问题
                    encoding = 'utf-8' if sys.platform != 'win32' else 'utf-8'
                    errors = 'ignore' if sys.platform == 'win32' else 'strict'
                    
                    result = subprocess.run(
                        [ffprobe, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path],
                        capture_output=True, text=True, timeout=10, encoding=encoding, errors=errors
                    )
                    
                    if result.returncode == 0 and result.stdout:
                        data = json.loads(result.stdout)
                        streams = data.get('streams', [])
                        for stream in streams:
                            if stream.get('codec_type') == 'video':
                                width = stream.get('width')
                                height = stream.get('height')
                                break
                        format_data = data.get('format', {})
                        duration = int(float(format_data.get('duration', 0))) if format_data.get('duration') else None
                    else:
                        logger.error(f"ffprobe failed with return code {result.returncode}, stderr: {result.stderr}")
                except subprocess.TimeoutExpired:
                    logger.error(f"ffprobe timeout for file: {file_path}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse ffprobe output: {str(e)}, stdout: {result.stdout[:200] if result.stdout else 'None'}")
                except Exception as e:
                    logger.error(f"Failed to get video properties: {str(e)}")
            elif media_type == "IMAGE":
                # 使用PIL获取图片属性
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        width, height = img.size
                except Exception as e:
                    logger.error(f"Failed to get image properties: {str(e)}")
            
            # 计算宽高比
            if width and height:
                ratio = round(width / height, 2) if height > 0 else None
            
            # 创建媒体记录
            media_data = {
                "name": file_name,
                "description": '',

                "type": media_type,
                "local_media_path": file_path.replace("\\", "/"),
                "file_size": file_size,
                "file_hash": file_hash,
                "duration": duration,
                "width": width,
                "height": height,
                "ratio": ratio,

                "remote_media_url": config.file_path_to_server_path(file_path),
                "group_id": group_id,
                "actor_id": actor_id,
            }
            
            new_media = MediaService.create(db, media_data)
            
            # 生成缩略图（图片和视频都支持）
            if new_media:
                thumb_path = config.get_thumbnail_path(new_media.id)
                ThumbnailUtils.generate_thumbnail(file_path, thumb_path, media_type, config.FFMPEG_PATH)
            
            return {"media": new_media, "is_new": True} if new_media else None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to add media from file: {str(e)}")
            return None
