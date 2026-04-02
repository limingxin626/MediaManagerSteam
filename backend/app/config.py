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
            "/asktao": cls.DATA_ROOT,
            "/av": "F:/AV",
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
    
    @classmethod
    def to_url_path(cls, file_path: str) -> str:
        """将系统绝对路径转换为服务器URL路径
        
        例如: E:/AskTao/data/video.mp4 -> /asktao/data/video.mp4
              F:/AV/movie.mp4 -> /av/movie.mp4
        """
        if not file_path:
            return ""
        
        # 统一使用正斜杠
        normalized_path = file_path.replace("\\", "/")
        
        # 遍历所有挂载点，找到匹配的并转换
        for url_prefix, system_path in cls.get_static_mounts().items():
            normalized_mount = system_path.replace("\\", "/")
            # 处理路径匹配（不区分大小写）
            if normalized_path.lower().startswith(normalized_mount.lower()):
                # 替换挂载路径为URL前缀
                relative_path = normalized_path[len(normalized_mount):]
                # 确保relative_path以/开头
                if relative_path and not relative_path.startswith("/"):
                    relative_path = "/" + relative_path
                return url_prefix + relative_path
        
        # 如果没有匹配到任何挂载点，返回原路径
        return file_path


# 创建全局配置实例
config = AppConfig()
