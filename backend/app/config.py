"""
应用配置模块 - 集中管理所有路径和配置
支持通过环境变量覆盖默认配置
"""
import os
from typing import Dict


class AppConfig:
    """应用配置类"""
    
    # 基础数据目录 - 可通过环境变量 ASKTAO_DATA_ROOT 覆盖
    DATA_ROOT: str = os.getenv("ASKTAO_DATA_ROOT", "E:/AskTao")
    
    # ffmpeg/ffprobe 路径 - 可通过环境变量覆盖
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "C:/Users/christluck/Documents/ffmpeg/bin/ffmpeg.exe")
    FFPROBE_PATH: str = os.getenv("FFPROBE_PATH", "C:/Users/christluck/Documents/ffmpeg/bin/ffprobe.exe")
    
    # 支持的媒体文件扩展名（统一管理）
    VIDEO_EXTENSIONS: set = {".mp4"}
    IMAGE_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif"}
    
    @classmethod
    def get_media_type(cls, file_path: str) -> str | None:
        """根据文件扩展名判断媒体类型"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in cls.VIDEO_EXTENSIONS:
            return "VIDEO"
        elif ext in cls.IMAGE_EXTENSIONS:
            return "IMAGE"
        return None
    
    # 静态文件挂载配置: {服务器路径: 系统目录}
    # 服务器路径不包含 DATA_ROOT，因为它们直接映射到 category
    @classmethod
    def get_static_mounts(cls) -> Dict[str, str]:
        """获取静态文件挂载配置"""
        mounts = {
            "/data": os.path.join(cls.DATA_ROOT, "data"),
        }
        return mounts
    
    @classmethod
    def get_upload_dir(cls) -> str:
        """获取手机上传文件的落地目录"""
        from datetime import date
        today = date.today()
        return os.path.join(cls.DATA_ROOT, "uploads", str(today.year), f"{today.month:02d}", f"{today.day:02d}")

    @classmethod
    def get_thumbs_dir(cls) -> str:
        """获取缩略图目录的系统绝对路径"""
        return os.path.join(cls.DATA_ROOT, "data", "thumbs")
    
    @classmethod
    def get_thumbnail_path(cls, media_id: int) -> str:
        """获取指定媒体ID的缩略图系统绝对路径"""
        return os.path.join(cls.get_thumbs_dir(), f"{media_id}.webp")
    
    @classmethod
    def get_actor_cover_dir(cls) -> str:
        """获取演员封面目录的系统绝对路径"""
        return os.path.join(cls.DATA_ROOT, "data", "actor_cover")
    
    @classmethod
    def get_actor_avatar_path(cls, actor_id: int) -> str:
        """获取指定演员ID的头像系统绝对路径"""
        return os.path.join(cls.get_actor_cover_dir(), f"{actor_id}.webp")


# 创建全局配置实例
config = AppConfig()
