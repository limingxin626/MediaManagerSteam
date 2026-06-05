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
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def _get_env(name: str, default: str = None) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        if default is not None:
            return default
        logger.error("环境变量 %s 未设置，无法启动。", name)
        sys.exit(1)
    return val


def _dir_name(path: str) -> str:
    """取目录的最后一级文件夹名（不区分大小写统一小写比较）"""
    return os.path.basename(os.path.normpath(path))


class AppConfig:
    """应用配置类"""

    DATA_ROOT: str = os.path.abspath(_get_env("DATA_ROOT"))
    UPLOAD_DIR: str = os.path.abspath(_get_env("UPLOAD_DIR"))

    # 额外静态挂载目录，分号分隔
    STATIC_DIRS: list = [
        os.path.abspath(d.strip()) for d in os.getenv("STATIC_DIRS", "").split(";") if d.strip()
    ]

    HOST: str = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"
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
        """启动时校验 ffmpeg/ffprobe:解析到绝对路径,并实际执行 -version 探活。
        任一失败则 fail-fast,避免运行中静默失败导致缩略图/元数据丢失。
        """
        import shutil as _shutil
        import subprocess as _sp

        for label in ("FFMPEG_PATH", "FFPROBE_PATH"):
            raw = getattr(cls, label)
            resolved = raw if os.path.isabs(raw) else _shutil.which(raw)
            if not resolved or not os.path.isfile(resolved):
                logger.error("%s 无法定位到可执行文件 (raw=%s, resolved=%s)。", label, raw, resolved)
                sys.exit(1)
            try:
                r = _sp.run([resolved, "-version"], capture_output=True,
                            timeout=5, text=True, encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.error("%s 探活失败 (%s): %s", label, resolved, e)
                sys.exit(1)
            if r.returncode != 0:
                logger.error("%s -version 返回非零 (%s, rc=%s): %s",
                             label, resolved, r.returncode, (r.stderr or "")[:200])
                sys.exit(1)
            setattr(cls, label, resolved)
            logger.info("%s OK: %s", label, resolved)

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
        """判断文件路径是否位于任何已挂载的静态目录下。

        DEPRECATED:新代码请用 register_relative()(原地把绝对路径分解成 repo_id + 相对路径)。
        本方法保留供 alembic downgrade / scripts 使用。
        """
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
        """将系统绝对路径转换为服务器 URL 路径。

        DEPRECATED:新代码请用 url_for(repo_id, relative_path)。
        本方法保留供 MediaUrlMixin 在 `__legacy__` 行 / 未注册 repo 上做兜底,以及 scripts 使用。
        """
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

    # ------------------------------------------------------------------ #
    # Repository 抽象 —— 把"挂载点"形式化到 DB 里(media.repo_id + 相对路径)
    # ------------------------------------------------------------------ #

    @classmethod
    def get_repositories(cls) -> Dict[str, str]:
        """{repo_id: abs_mount_path}。UPLOAD_DIR + STATIC_DIRS 一视同仁,都用 basename.lower() 作 id。

        DATA_ROOT 不是 media repo(只放 thumbs/avatar/db),不参与。
        启动时 check_mount_names() 已保证 basename 全局唯一,这里直接覆盖也不会冲突。
        """
        repos: Dict[str, str] = {}
        for path in [cls.UPLOAD_DIR] + cls.STATIC_DIRS:
            repos[_dir_name(path).lower()] = path
        return repos

    @classmethod
    def default_repo_id(cls) -> str:
        """默认 repo(新上传文件落地的 repo)的 id = basename(UPLOAD_DIR).lower()。"""
        return _dir_name(cls.UPLOAD_DIR).lower()

    @classmethod
    def resolve_to_absolute(cls, repo_id: str, relative_path: str) -> Optional[str]:
        """(repo_id, relative_path) → 本机绝对路径。未知 repo 返回 None。

        relative_path 在 DB 里永远以 forward-slash 存储;这里转成 os.sep 再 join。
        单段相对路径(如 "x.mp4")也合法,直接落在 repo 根目录下。
        """
        if not repo_id:
            return None
        repos = cls.get_repositories()
        mount = repos.get(repo_id)
        if mount is None:
            return None
        if not relative_path:
            return mount
        rel = relative_path.lstrip("/").replace("/", os.sep)
        return os.path.join(mount, rel)

    @classmethod
    def register_relative(cls, absolute_path: str) -> Tuple[str, str]:
        """inverse of resolve_to_absolute。按 mount path 长度 DESC 匹配,处理嵌套 mount。

        命中 → 返回 (repo_id, forward-slash 相对路径)。
        未命中 → ValueError。调用方对新上传文件应先 copy 进 UPLOAD_DIR 再调用。
        """
        if not absolute_path:
            raise ValueError("Empty path")
        norm = absolute_path.replace("\\", "/")
        norm_lc = norm.lower()
        candidates = sorted(
            cls.get_repositories().items(),
            key=lambda kv: len(kv[1]),
            reverse=True,
        )
        for rid, mount in candidates:
            mount_norm = mount.replace("\\", "/").rstrip("/")
            mount_lc = mount_norm.lower()
            if norm_lc == mount_lc:
                return rid, ""
            if norm_lc.startswith(mount_lc + "/"):
                rel = norm[len(mount_norm):].lstrip("/")
                return rid, rel
        raise ValueError(f"Path not under any registered repo: {absolute_path}")

    @classmethod
    def url_for(cls, repo_id: str, relative_path: str) -> str:
        """(repo_id, relative_path) → "/{mount_basename}/relative/path" 的 HTTP URL。

        URL 前缀仍用 mount 的 basename(跟 FastAPI StaticFiles 挂载方式一致),
        不直接用 repo_id 是为了未来 repo_id 可以脱离 basename 而 URL 不变。
        未知 repo 返回空串,由调用方决定兜底。
        """
        if not repo_id:
            return ""
        repos = cls.get_repositories()
        mount = repos.get(repo_id)
        if mount is None:
            return ""
        prefix = _dir_name(mount)
        rel = (relative_path or "").lstrip("/")
        if not rel:
            return f"/{prefix}"
        return f"/{prefix}/{rel}"

    @classmethod
    def get_db_path(cls) -> str:
        return os.path.join(cls.DATA_ROOT, "db.sqlite3")

# 创建全局配置实例
config = AppConfig()
