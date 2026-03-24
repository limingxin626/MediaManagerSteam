from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from app.models import Group, Actor, Media
from app.config import config


class GroupService:
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Group]:
        return db.query(Group).offset(skip).limit(limit).all()

    @staticmethod
    def get_count(db: Session) -> int:
        from sqlalchemy import func
        return db.query(func.count(Group.id)).scalar() or 0

    @staticmethod
    def get_by_id(db: Session, group_id: int) -> Optional[Group]:
        return db.query(Group).filter(Group.id == group_id).first()

    @staticmethod
    def get_detail(db: Session, group_id: int) -> Optional[Group]:
        return db.query(Group).options(
            joinedload(Group.media),
            joinedload(Group.actor)
        ).filter(Group.id == group_id).first()

    @staticmethod
    def get_by_actor_id(db: Session, actor_id: int) -> List[Group]:
        return db.query(Group).filter(Group.actor_id == actor_id).all()

    @staticmethod
    def create(db: Session, group_data: Dict[str, Any]) -> Optional[Group]:
        if "actor_id" in group_data and group_data["actor_id"]:
            actor = db.query(Actor).filter(Actor.id == group_data["actor_id"]).first()
            if not actor:
                return None

        db_group = Group(**group_data)
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        return db_group

    @staticmethod
    def update(db: Session, group_id: int, update_data: Dict[str, Any]) -> Optional[Group]:
        db_group = db.query(Group).filter(Group.id == group_id).first()
        if not db_group:
            return None

        if "actor_id" in update_data and update_data["actor_id"] is not None:
            actor = db.query(Actor).filter(Actor.id == update_data["actor_id"]).first()
            if not actor:
                return None

        for key, value in update_data.items():
            setattr(db_group, key, value)

        db.commit()
        db.refresh(db_group)
        return db_group

    @staticmethod
    def delete(db: Session, group_id: int) -> bool:
        db_group = db.query(Group).filter(Group.id == group_id).first()
        if not db_group:
            return False

        db.query(Media).filter(Media.group_id == group_id).delete()

        db.delete(db_group)
        db.commit()
        return True

    @staticmethod
    def apply_scan_results(db: Session, group_id: int, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """应用扫描结果，执行实际的数据操作"""
        try:
            from app.services.media import MediaService
            
            # 验证group是否存在
            db_group = GroupService.get_by_id(db, group_id)
            if not db_group:
                return {"success": False, "message": "分组不存在"}
            
            # 统计信息
            added_count = 0
            updated_count = 0
            deleted_count = 0
            total_size = 0
            
            # 处理新文件
            for file_info in scan_results.get("new_files", []):
                try:
                    result = MediaService.add_media_from_file(
                        db, 
                        file_info["path"], 
                        group_id, 
                        db_group.actor_id
                    )
                    if result and result.get("is_new", False):
                        added_count += 1
                        total_size += result["media"].file_size
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to add new file {file_info['path']}: {str(e)}")
            
            # 处理重命名的文件
            for file_info in scan_results.get("renamed_files", []):
                try:
                    media = db.query(Media).filter(Media.id == file_info["media_id"]).first()
                    if media:
                        media.local_media_path = file_info["new_path"]
                        media.name = file_info["new_name"]
                        updated_count += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to update renamed file {file_info['new_path']}: {str(e)}")
            
            # 处理缺失的文件
            for file_info in scan_results.get("missing_files", []):
                try:
                    media = db.query(Media).filter(Media.id == file_info["media_id"]).first()
                    if media:
                        db.delete(media)
                        deleted_count += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to delete missing file {file_info['path']}: {str(e)}")
            
            # 更新group的媒体数量和大小
            if added_count > 0 or deleted_count > 0:
                # 重新计算媒体数量和大小
                media_list = db.query(Media).filter(Media.group_id == group_id).all()
                db_group.media_cnt = len(media_list)
                db_group.size = sum(media.file_size for media in media_list if media.file_size)
            
            # 提交更改
            db.commit()
            
            return {
                "success": True,
                "message": "应用扫描结果成功",
                "group_name": db_group.name,
                "added_count": added_count,
                "updated_count": updated_count,
                "deleted_count": deleted_count,
                "total_size": total_size
            }
        except Exception as e:
            db.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to apply scan results: {str(e)}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def scan_group(db: Session, group_id: int) -> Dict[str, Any]:
        """扫描group文件夹，检查媒体文件状态，不进行数据修改"""
        try:
            import os
            import hashlib
            
            # 验证group是否存在
            db_group = GroupService.get_by_id(db, group_id)
            if not db_group:
                return {"success": False, "message": "分组不存在"}
            
            # 验证actor是否存在
            if not db_group.actor_id:
                return {"success": False, "message": "分组没有关联演员"}
            
            # 构建group文件夹路径
            actor = db_group.actor
            group_folder = config.get_group_folder(actor.category.value, actor.name, db_group.name)
            
            # 检查group文件夹是否存在
            if not os.path.exists(group_folder):
                return {"success": False, "message": "分组文件夹不存在"}
            
            # 扫描文件夹中的媒体文件
            new_files = []  # 文件夹内的媒体文件不存在于数据库中
            renamed_files = []  # 名字变了，但是通过hash能找到
            missing_files = []  # 数据库中的数据找不到对应的文件
            
            # 获取数据库中该group的所有媒体
            db_media_list = db.query(Media).filter(Media.group_id == group_id).all()
            db_media_dict = {media.local_media_path: media for media in db_media_list}
            db_media_hash_dict = {media.file_hash: media for media in db_media_list if media.file_hash}
            
            # 只检查文件夹中的直接文件，不递归遍历子文件夹
            try:
                for item in os.listdir(group_folder):
                    file_path = os.path.join(group_folder, item)
                    # 只处理文件，跳过文件夹
                    if os.path.isfile(file_path):
                        # 检查文件类型（使用统一配置）
                        media_type = config.get_media_type(file_path)
                        
                        if media_type:
                            try:
                                # 标准化文件路径
                                normalized_path = file_path.replace("\\", "/")
                                
                                # 检查1：文件夹内的媒体文件不存在于数据库中
                                if normalized_path not in db_media_dict:
                                    # 计算文件hash
                                    file_size = os.path.getsize(file_path)
                                    file_hash = None
                                    
                                    if file_size < 100 * 1024 * 1024:  # 100MB
                                        hasher = hashlib.md5()
                                        with open(file_path, 'rb') as f:
                                            for chunk in iter(lambda: f.read(4096), b''):
                                                hasher.update(chunk)
                                        file_hash = hasher.hexdigest()
                                    else:
                                        file_hash = str(file_size)
                                    
                                    # 检查2：名字变了，但是通过hash能找到
                                    if file_hash and file_hash in db_media_hash_dict:
                                        old_media = db_media_hash_dict[file_hash]
                                        renamed_files.append({
                                            "old_path": old_media.local_media_path,
                                            "new_path": normalized_path,
                                            "media_id": old_media.id,
                                            "old_name": old_media.name,
                                            "new_name": os.path.splitext(os.path.basename(file_path))[0]
                                        })
                                    else:
                                        new_files.append({
                                            "path": normalized_path,
                                            "name": os.path.splitext(os.path.basename(file_path))[0],
                                            "file_hash": file_hash,
                                            "type": media_type
                                        })
                                else:
                                    # 文件存在于数据库中，从db_media_dict中移除
                                    del db_media_dict[normalized_path]
                            except Exception as e:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.error(f"Failed to process file {file_path}: {str(e)}")
            except PermissionError:
                return {"success": False, "message": "没有权限访问该文件夹"}
            
            # 记录重命名文件的旧路径，用于跳过检查
            renamed_old_paths = {item["old_path"] for item in renamed_files}
            
            # 检查3：数据库中的数据找不到对应的文件（跳过重命名的文件）
            for local_media_path, media in db_media_dict.items():
                if local_media_path in renamed_old_paths:
                    continue
                if not os.path.exists(local_media_path.replace("/", "\\")):
                    missing_files.append({
                        "path": local_media_path,
                        "name": media.name,
                        "media_id": media.id
                    })
            
            return {
                "success": True,
                "message": "扫描完成",
                "group_name": db_group.name,
                "new_files": new_files,
                "renamed_files": renamed_files,
                "missing_files": missing_files,
                "summary": {
                    "new_count": len(new_files),
                    "renamed_count": len(renamed_files),
                    "missing_count": len(missing_files)
                }
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to scan group: {str(e)}")
            return {"success": False, "message": str(e)}
