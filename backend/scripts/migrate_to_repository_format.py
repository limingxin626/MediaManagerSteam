#!/usr/bin/env python3
r"""
迁移脚本：将 Media.file_path 从绝对路径转换为相对路径 + repo_id 格式

旧格式：E:/Note\uploads\2026\04\06\1774003234291A1E713BA063312AD.jpg
新格式：repo_id="uploads", file_path="uploads/2026/04/06/1774003234291A1E713BA063312AD.jpg"

使用：
    cd backend
    uv run scripts/migrate_to_repository_format.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Media, SessionLocal
from app.config import AppConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_repositories() -> Dict[str, Dict[str, str]]:
    """加载 repositories.json，返回 {repo_id: {平台: 路径}}
    
    这样可以支持跨平台的旧路径识别。
    """
    repos_file = os.path.join(AppConfig.DATA_ROOT, "repositories.json")
    
    if not os.path.isfile(repos_file):
        logger.error(f"repositories.json 不存在: {repos_file}")
        sys.exit(1)
    
    with open(repos_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    repos = {}
    for repo_id, entry in data.get("repositories", {}).items():
        paths = entry.get("paths", {})
        repos[repo_id] = {
            plat: os.path.abspath(p.replace("/", os.sep))
            for plat, p in paths.items()
        }
    
    logger.info(f"加载了 {len(repos)} 个 repository: {list(repos.keys())}")
    return repos


def parse_old_file_path(file_path: str, repos: Dict[str, Dict[str, str]]) -> Optional[Tuple[str, str]]:
    """
    解析旧格式的绝对路径，返回 (repo_id, 相对路径)
    
    支持跨平台路径识别：
    - E:/Note\\uploads\\2026\\04\\06\\xxx.jpg -> ("uploads", "2026/04/06/xxx.jpg")
    - /Volumes/AV/archive/2026\\01\\01\\yyy.mp4 -> ("av", "archive/2026/01/01/yyy.mp4")
    
    注意：返回的相对路径不包含 repo_id 本身，仅是该 repo 内的相对路径
    """
    if not file_path:
        return None
    
    # 标准化路径分隔符为统一格式（用 / 便于比较）
    normalized = file_path.replace("\\", "/")
    
    # 尝试匹配每个 repository 的所有平台
    for repo_id, platforms in repos.items():
        for plat, repo_root in platforms.items():
            # 标准化 repo_root
            repo_root_norm = repo_root.replace("\\", "/").replace(os.sep, "/")
            
            # 检查是否匹配（大小写不敏感的 Windows 路径）
            if normalized.lower().startswith(repo_root_norm.lower() + "/") or \
               normalized.lower() == repo_root_norm.lower():
                # 计算相对路径
                if normalized.lower() == repo_root_norm.lower():
                    rel_path = ""
                else:
                    # 去掉 repo_root 前缀后的部分（保留大小写原样）
                    prefix_len = len(repo_root_norm) + 1
                    rel_path = normalized[prefix_len:]
                
                logger.debug(f"匹配 {file_path} 到 {repo_id}(平台={plat}), 相对路径={rel_path}")
                return repo_id, rel_path
    
    # 启发式兜底：尝试从路径名识别 repo_id
    # 例如：E:/Note/uploads/2026/04/06/xxx.jpg -> 看 "uploads" 是否是某个 repo_id
    path_parts = normalized.split("/")
    for i, part in enumerate(path_parts):
        part_lower = part.lower()
        for repo_id in repos.keys():
            if repo_id.lower() == part_lower:
                logger.info(f"使用启发式匹配: {file_path} -> repo_id={repo_id}")
                # part 之后的路径部分作为相对路径
                rel_path = "/".join(path_parts[i+1:])
                return repo_id, rel_path
    
    logger.warning(f"无法匹配 file_path 到任何 repository: {file_path}")
    return None


def migrate():
    """执行迁移"""
    repos = load_repositories()
    
    db = SessionLocal()
    try:
        # 查询所有 Media 记录
        all_media = db.query(Media).all()
        logger.info(f"总共 {len(all_media)} 条 Media 记录")
        
        if not all_media:
            logger.info("没有 Media 记录，无需迁移")
            return
        
        # 统计信息
        migrated = 0
        failed = 0
        already_new_format = 0
        
        for media in all_media:
            old_path = media.file_path
            
            # 判断是否已是新格式（含有仓库 id）
            if media.repo_id and media.repo_id != "uploads":
                already_new_format += 1
            
            # 尝试解析旧格式
            result = parse_old_file_path(old_path, repos)
            
            if result:
                repo_id, rel_path = result
                logger.info(f"[{media.id}] {old_path}")
                logger.info(f"         -> repo_id={repo_id}, file_path={rel_path}")
                
                media.repo_id = repo_id
                media.file_path = rel_path
                migrated += 1
            else:
                logger.error(f"[{media.id}] 迁移失败: {old_path}")
                failed += 1
        
        # 提交更改
        if migrated > 0:
            db.commit()
            logger.info("✅ 迁移完成！")
        else:
            logger.info("无需更改")
        
        logger.info(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"迁移统计:")
        logger.info(f"  已迁移: {migrated}")
        logger.info(f"  已是新格式: {already_new_format}")
        logger.info(f"  失败: {failed}")
        logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if failed > 0:
            logger.warning("⚠️  有迁移失败的记录，请检查 repositories.json 配置")
            sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        logger.error(f"迁移失败: {e}", exc_info=True)
        sys.exit(1)
