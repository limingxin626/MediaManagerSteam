from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models import Actor
from app.config import config
from app.utils import current_media_list, current_group_list
import logging

logger = logging.getLogger(__name__)


class ActorService:
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Actor]:
        try:
            return db.query(Actor).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to get all actors: {str(e)}")
            return []

    @staticmethod
    def _apply_filters(query, filters):
        """应用过滤条件"""
        if filters:
            if "name" in filters and filters["name"]:
                query = query.filter(Actor.name.like(f"%{filters['name']}%"))

            if "min_score" in filters and filters["min_score"] is not None:
                query = query.filter(Actor.rating >= filters["min_score"])

            if "max_score" in filters and filters["max_score"] is not None:
                query = query.filter(Actor.rating <= filters["max_score"])
        return query

    @staticmethod
    def search(db: Session, filters: Dict[str, Any] = None, skip: int = 0, limit: int = 100,
              sort_by: str = "id", sort_order: str = "asc") -> List[Actor]:
        try:
            query = db.query(Actor)
            query = ActorService._apply_filters(query, filters)

            sort_column = getattr(Actor, sort_by, Actor.id)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Failed to search actors: {str(e)}")
            return []

    @staticmethod
    def search_count(db: Session, filters: Dict[str, Any] = None) -> int:
        try:
            query = db.query(func.count(Actor.id))
            query = ActorService._apply_filters(query, filters)
            return query.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to count actors: {str(e)}")
            return 0

    @staticmethod
    def get_by_id(db: Session, actor_id: int) -> Optional[Actor]:
        """获取演员基本信息（不包含分组）"""
        try:
            return db.query(Actor).filter(Actor.id == actor_id).first()
        except Exception as e:
            logger.error(f"Failed to get actor by id {actor_id}: {str(e)}")
            return None

    @staticmethod
    def get_by_id_with_groups(db: Session, actor_id: int) -> Optional[Actor]:
        """获取演员详情（包含分组和媒体，媒体只获取前100个）"""
        try:
            from app.models import Media
            
            actor = db.query(Actor).options(
                joinedload(Actor.groups)
            ).filter(Actor.id == actor_id).first()
            
            if actor:
                # 单独获取前100个media
                media_list = db.query(Media).filter(
                    Media.actor_id == actor_id
                ).order_by(Media.created_at.desc()).limit(100).all()
                actor.media = media_list
                
                # 更新全局媒体列表
                if actor.media:
                    global current_media_list
                    current_media_list = [media.id for media in actor.media]
                    logger.info(f"Updated current_media_list with {len(current_media_list)} media items for actor {actor.name}")

                # 更新全局分组列表
                if actor.groups:
                    global current_group_list
                    current_group_list = [group.id for group in actor.groups]
                    logger.info(f"Updated current_group_list with {len(current_group_list)} groups for actor {actor.name}")

            return actor
        except Exception as e:
            logger.error(f"Failed to get actor with groups by id {actor_id}: {str(e)}")
            return None

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Actor]:
        try:
            return db.query(Actor).filter(Actor.name == name).first()
        except Exception as e:
            logger.error(f"Failed to get actor by name '{name}': {str(e)}")
            return None

    @staticmethod
    def create(db: Session, create_data: Dict[str, Any]) -> Optional[Actor]:
        try:
            db_actor = Actor(**create_data)
            db.add(db_actor)
            db.commit()
            db.refresh(db_actor)
            logger.info(f"Created actor: {db_actor.name} (ID: {db_actor.id})")
            return db_actor
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create actor: {str(e)}")
            return None

    @staticmethod
    def update(db: Session, actor_id: int, update_data: Dict[str, Any]) -> Optional[Actor]:
        try:
            db_actor = db.query(Actor).filter(Actor.id == actor_id).first()
            if not db_actor:
                return None

            for key, value in update_data.items():
                setattr(db_actor, key, value)

            db.commit()
            db.refresh(db_actor)
            logger.info(f"Updated actor: {db_actor.name} (ID: {db_actor.id})")
            return db_actor
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update actor {actor_id}: {str(e)}")
            return None

    @staticmethod
    def delete(db: Session, actor_id: int) -> bool:
        try:
            db_actor = db.query(Actor).filter(Actor.id == actor_id).first()
            if not db_actor:
                return False

            db.delete(db_actor)
            db.commit()
            logger.info(f"Deleted actor: {db_actor.name} (ID: {db_actor.id})")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete actor {actor_id}: {str(e)}")
            return False

    @staticmethod
    def batch_create(db: Session, actors_data: List[Dict[str, Any]]) -> List[Actor]:
        """批量创建演员"""
        try:
            created_actors = []
            for actor_data in actors_data:
                db_actor = Actor(**actor_data)
                db.add(db_actor)
                created_actors.append(db_actor)
            db.commit()
            for actor in created_actors:
                db.refresh(actor)
                logger.info(f"Created actor: {actor.name} (ID: {actor.id})")
            return created_actors
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to batch create actors: {str(e)}")
            return []

    @staticmethod
    def batch_update(db: Session, actors_data: List[Dict[str, Any]]) -> List[Actor]:
        """批量更新演员"""
        try:
            updated_actors = []
            for actor_data in actors_data:
                if "id" not in actor_data:
                    continue
                actor_id = actor_data["id"]
                update_data = {k: v for k, v in actor_data.items() if k != "id"}
                db_actor = ActorService.update(db, actor_id, update_data)
                if db_actor:
                    updated_actors.append(db_actor)
            return updated_actors
        except Exception as e:
            logger.error(f"Failed to batch update actors: {str(e)}")
            return []

    @staticmethod
    def batch_delete(db: Session, actor_ids: List[int]) -> int:
        """批量删除演员"""
        try:
            deleted_count = db.query(Actor).filter(Actor.id.in_(actor_ids)).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Batch deleted {deleted_count} actors")
            return deleted_count
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to batch delete actors: {str(e)}")
            return 0

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """获取演员统计信息"""
        try:
            total = db.query(func.count(Actor.id)).scalar() or 0
            by_category = db.query(Actor.category, func.count(Actor.id)).group_by(Actor.category).all()
            by_country = db.query(Actor.country, func.count(Actor.id)).group_by(Actor.country).all()
            
            return {
                "total": total,
                "by_category": dict(by_category),
                "by_country": dict(by_country)
            }
        except Exception as e:
            logger.error(f"Failed to get actor statistics: {str(e)}")
            return {"total": 0, "by_category": {}, "by_country": {}}

    @staticmethod
    def scan_actor(db: Session, actor_id: int) -> Dict[str, Any]:
        """扫描演员文件夹，创建分组并添加媒体"""
        try:
            from app.models import Group, Media
            from app.services.group import GroupService
            import os
            import datetime
            
            # 验证演员是否存在
            actor = ActorService.get_by_id(db, actor_id)
            if not actor:
                return {"success": False, "message": "演员不存在"}
            
            # 获取演员文件夹路径
            actor_folder = config.get_actor_folder(actor.category.value, actor.name)
            
            # 检查演员文件夹是否存在
            if not os.path.exists(actor_folder):
                return {"success": False, "message": "演员文件夹不存在"}
            
            # 获取演员文件夹下的所有子文件夹
            folders = []
            for item in os.listdir(actor_folder):
                item_path = os.path.join(actor_folder, item)
                if os.path.isdir(item_path):
                    folders.append(item)
            
            # 为每个文件夹创建group
            created_groups = []
            for folder_name in folders:
                if folder_name.startswith("sk") or folder_name == "修复" or folder_name == "原档":
                    continue
                # 检查是否已存在同名group
                existing_groups = db.query(Group).filter(
                    Group.actor_id == actor_id,
                    Group.name == folder_name
                ).all()
                
                if not existing_groups:
                    # 创建新group
                    group_data = {
                        "name": folder_name,
                        "description": f"{actor.name}的{folder_name}分组",
                        "actor_id": actor_id,
                        "date": datetime.date.today(),
                        "media_cnt": 0
                    }
                    new_group = GroupService.create(db, group_data)
                    if new_group:
                        created_groups.append(new_group)
            
            # 扫描每个group文件夹，添加媒体到数据库
            total_added_media = 0
            total_skipped_media = 0
            total_failed_media = 0
            groups = GroupService.get_by_actor_id(db, actor_id)
            
            for group in groups:
                # 使用新的GroupService.scan_group方法扫描group文件夹
                scan_result = GroupService.scan_group(db, group.id)
                if scan_result["success"]:
                    total_added_media += scan_result.get("added_media", 0)
                    total_skipped_media += scan_result.get("skipped_media", 0)
                    total_failed_media += scan_result.get("failed_media", 0)
            
            # 检测失效的媒体（数据库中存在但文件系统中不存在）
            invalid_media = []
            all_media = db.query(Media).filter(Media.actor_id == actor_id).all()
            for media in all_media:
                if media.local_media_path and not os.path.exists(media.local_media_path):
                    invalid_media.append({
                        "id": media.id,
                        "name": media.name,
                    })
            
            # 构建返回消息
            message_parts = [f"扫描完成"]
            if invalid_media:
                message_parts.append(f"，发现{len(invalid_media)}个失效媒体")
            
            return {
                "success": True,
                "message": "".join(message_parts),
                "folders_found": len(folders),
                "groups_created": len(created_groups),
                "media_added": total_added_media,
                "media_skipped": total_skipped_media,
                "media_failed": total_failed_media,
                "invalid_media": invalid_media
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to scan actor: {str(e)}")
            return {"success": False, "message": str(e)}
