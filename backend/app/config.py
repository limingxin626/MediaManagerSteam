"""
应用配置模块 - 集中管理所有路径和配置

环境变量：
  DATA_ROOT     — 数据库 + 缩略图目录（必填，无默认值）
  UPLOAD_DIR    — 上传文件落地目录（必填，无默认值）
  STATIC_DIRS   — 额外静态挂载目录，分号分隔，可选（如 F:/AV;G:/Movies）
    HOST          — 服务监听地址，默认 127.0.0.1（仅本机访问）
  PORT          — 服务端口，默认 8002
  FFMPEG_PATH   — ffmpeg 可执行文件路径，默认使用 PATH 中的
  FFPROBE_PATH  — ffprobe 可执行文件路径，默认使用 PATH 中的
"""
import logging
import os
import sys
from typing import Dict

logger = logging.getLogger(__name__)


def _require_env(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        logger.error("环境变量 %s 未设置，无法启动。", name)
        sys.exit(1)
    return val


def _dir_name(path: str) -> str:
    """取目录的最后一级文件夹名（不区分大小写统一小写比较）"""
    return os.path.basename(os.path.normpath(path))


class AppConfig:
    """应用配置类"""

    DATA_ROOT: str = os.path.abspath(_require_env("DATA_ROOT"))
    UPLOAD_DIR: str = os.path.abspath(_require_env("UPLOAD_DIR"))

    # 额外静态挂载目录，分号分隔
    STATIC_DIRS: list = [
        os.path.abspath(d.strip()) for d in os.getenv("STATIC_DIRS", "").split(";") if d.strip()
    ]

    HOST: str = os.getenv("HOST", "127.0.0.1").strip() or "127.0.0.1"
    PORT: int = int(os.getenv("PORT", "8002"))

    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    FFPROBE_PATH: str = os.getenv("FFPROBE_PATH", "ffprobe")

    ALLOWED_ORIGINS: list = [
        "http://127.0.0.1",
        "http://localhost",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:8002",
        "http://localhost:8002",
    ]

    # 支持的媒体文件扩展名
    VIDEO_EXTENSIONS: set = {".mp4"}
    IMAGE_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".gif"}

    @classmethod
    def check_paths(cls) -> None:
        """启动时检查关键路径，ffmpeg 不在 PATH 时打印 warning。"""
        for label, path in [("FFMPEG_PATH", cls.FFMPEG_PATH), ("FFPROBE_PATH", cls.FFPROBE_PATH)]:
            # 如果是绝对路径则检查文件是否存在；如果是命令名则跳过（交给运行时报错）
            if os.path.isabs(path) and not os.path.isfile(path):
                logger.warning(
                    "%s 指向的文件不存在: %s — 缩略图生成和媒体信息提取将静默失败。",
                    label, path,
                )

    @classmethod
    def get_static_mounts(cls) -> Dict[str, str]:
        """
        返回 {url_prefix: system_path} 的挂载映射。
        DATA_ROOT、UPLOAD_DIR、STATIC_DIRS 均以文件夹名为 URL 前缀。
        启动时已通过 check_mount_names() 保证无重名。
        """
        mounts: Dict[str, str] = {}
        for path in [cls.DATA_ROOT, cls.UPLOAD_DIR] + cls.STATIC_DIRS:
            name = _dir_name(path)
            mounts[f"/{name}"] = path
        return mounts

    @classmethod
    def check_mount_names(cls) -> None:
        """检查所有挂载目录的文件夹名是否重复，重复则报错退出。"""
        all_dirs = [cls.DATA_ROOT, cls.UPLOAD_DIR] + cls.STATIC_DIRS
        seen: Dict[str, str] = {}
        for path in all_dirs:
            name = _dir_name(path).lower()
            if name in seen:
                logger.error(
                    "挂载目录名称冲突：'%s' 和 '%s' 的文件夹名相同（%s），无法启动。"
                    " 请重命名其中一个目录或使用子目录。",
                    seen[name], path, name,
                )
                sys.exit(1)
            seen[name] = path

    @classmethod
    def get_media_type(cls, file_path: str) -> str | None:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in cls.VIDEO_EXTENSIONS:
            return "VIDEO"
        elif ext in cls.IMAGE_EXTENSIONS:
            return "IMAGE"
        return None

    @classmethod
    def get_upload_dir(cls) -> str:
        """获取按日期分组的上传落地目录"""
        from datetime import date
        today = date.today()
        return os.path.join(cls.UPLOAD_DIR, str(today.year), f"{today.month:02d}", f"{today.day:02d}")

    @classmethod
    def get_thumbs_dir(cls) -> str:
        return os.path.join(cls.DATA_ROOT, "thumbs")

    @classmethod
    def get_thumbnail_path(cls, media_id: int) -> str:
        return os.path.join(cls.get_thumbs_dir(), f"{media_id}.webp")

    @classmethod
    def get_actor_cover_dir(cls) -> str:
        return os.path.join(cls.DATA_ROOT, "actor_cover")

    @classmethod
    def get_actor_avatar_path(cls, actor_id: int) -> str:
        return os.path.join(cls.get_actor_cover_dir(), f"{actor_id}.webp")

    @classmethod
    def _data_root_prefix(cls) -> str:
        return f"/{_dir_name(cls.DATA_ROOT)}"

    @classmethod
    def get_thumbnail_url(cls, media_id: int) -> str:
        return f"{cls._data_root_prefix()}/thumbs/{media_id}.webp"

    @classmethod
    def get_actor_avatar_url(cls, actor_id: int) -> str:
        return f"{cls._data_root_prefix()}/actor_cover/{actor_id}.webp"

    @classmethod
    def is_mounted_path(cls, file_path: str) -> bool:
        """判断文件路径是否位于任何已挂载的静态目录下"""
        if not file_path:
            return False
        normalized = file_path.replace("\\", "/").lower()
        for system_path in cls.get_static_mounts().values():
            normalized_mount = system_path.replace("\\", "/").lower()
            if normalized.startswith(normalized_mount):
                return True
        return False

    @classmethod
    def to_url_path(cls, file_path: str) -> str:
        """将系统绝对路径转换为服务器 URL 路径"""
        if not file_path:
            return ""
        normalized_path = file_path.replace("\\", "/")
        for url_prefix, system_path in cls.get_static_mounts().items():
            normalized_mount = system_path.replace("\\", "/")
            if normalized_path.lower().startswith(normalized_mount.lower()):
                relative_path = normalized_path[len(normalized_mount):]
                if relative_path and not relative_path.startswith("/"):
                    relative_path = "/" + relative_path
                return url_prefix + relative_path
        return file_path

    @classmethod
    def get_db_path(cls) -> str:
        return os.path.join(cls.DATA_ROOT, "db.sqlite3")

    @classmethod
    def get_dashboard_md_path(cls) -> str:
        return os.path.join(cls.DATA_ROOT, "dashboard.md")


DASHBOARD_DEFAULT_CONTENT = "# 当前状态\n\n"


# 创建全局配置实例
config = AppConfig()
