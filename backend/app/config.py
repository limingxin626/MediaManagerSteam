"""
应用配置模块 - 集中管理所有路径和配置

配置来源(优先级 高→低):
  1. 真实环境变量(含 `api.py --data-root` 注入的、shell 里 export 的)
  2. 项目本地 `backend/.env`(gitignored;复制 `.env.example` 而来)
  本模块在 import 时即 `load_dotenv(backend/.env, override=False)` —— 真实环境变量
  永远优先,.env 只补缺。因为 `app.models` → `app.config`,**所有**走 `from app.*`
  的入口(api.py / alembic / scripts/*)import 时自动加载,无需各自调,切 instance
  只改 `backend/.env` 里的 DATA_ROOT 即可。详见 README / CLAUDE.md。

环境变量：
  DATA_ROOT     — 数据库 + 缩略图 + repositories.json 所在目录(必填,无默认)
  HOST          — 服务监听地址,默认 0.0.0.0
  PORT          — 服务端口,默认 8002
  FFMPEG_PATH   — ffmpeg 可执行文件路径,默认走 PATH
  FFPROBE_PATH  — ffprobe 可执行文件路径,默认走 PATH

Repository 配置:
  原 UPLOAD_DIR / STATIC_DIRS 两个 env vars 已废弃。挂载点定义改为
  `<DATA_ROOT>/repositories.json`,Backend 与 Mac 端共享。schema:

      {
        "version": 1,
        "default_repo_id": "uploads",
        "repositories": {
          "uploads": {
            "human_name": "Uploads",
            "paths": {"windows": "E:/Note/Uploads", "darwin": "/Volumes/Note/Uploads"}
          },
        }
      }

  - 平台 key: win32→windows / darwin→darwin / 其余→linux
  - 路径用 forward-slash 写,Windows 也认,避免 JSON 转义反斜杠
  - default_repo_id 决定新上传文件落地的 repo
"""
import json
import logging
import os
import sys
from typing import Dict, Optional, Tuple

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 项目本地 .env(backend/.env)。本文件在 app/ 下,parent 的 parent 即 backend/。
# override=False → os.environ 里已有的值(真实 env、api.py --data-root 注入的、
# alembic 的 ALEMBIC_SKIP_REPO_LOAD 哨兵)都不被 .env 覆盖,.env 只填缺。
# 必须在下面读 DATA_ROOT 之前执行;.env 不存在则静默(允许纯靠真实 env 跑)。
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=False)


def _get_env(name: str, default: str = None) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        if default is not None:
            return default
        logger.error(
            "环境变量 %s 未设置,无法启动。"
            "请在 backend/.env 里设置(复制 .env.example),或传 --data-root,"
            "或 %s=... 临时注入。",
            name, name,
        )
        sys.exit(1)
    return val


def _current_platform_key() -> str:
    """sys.platform → repositories.json 里 paths 的子 key。"""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


# repositories.json 文件名(同时被 alembic seed migration 引用,改名要同步)
REPOSITORIES_FILENAME = "repositories.json"


def _load_repositories(data_root: str) -> Tuple[Dict[str, str], str]:
    """读 `<data_root>/repositories.json`,返回 (repos, default_repo_id)。

    repos: {repo_id: 当前平台的绝对路径}。其他平台的 path 在本进程里不需要。
    任何解析失败 / schema 不对 / 当前平台缺路径 → fail-fast sys.exit(1)。
    """
    if not os.path.isdir(data_root):
        logger.error(
            "DATA_ROOT=%s 不存在。请运行 `uv run scripts/init_data_root.py` 初始化。",
            data_root,
        )
        sys.exit(1)
    path = os.path.join(data_root, REPOSITORIES_FILENAME)
    if not os.path.isfile(path):
        logger.error(
            "%s 不存在。请运行 `uv run scripts/init_data_root.py` 初始化。",
            path,
        )
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error("%s 解析失败: %s", path, e)
        sys.exit(1)

    version = data.get("version")
    if version != 1:
        logger.error("%s 版本号不匹配,期望 1,实际 %r", path, version)
        sys.exit(1)

    raw_repos = data.get("repositories")
    if not isinstance(raw_repos, dict) or not raw_repos:
        logger.error("%s 缺少 repositories 字段或为空", path)
        sys.exit(1)

    default_repo_id = data.get("default_repo_id")
    if not default_repo_id or default_repo_id not in raw_repos:
        logger.error(
            "%s default_repo_id=%r 无效(必须是 repositories 里的一个 key)",
            path, default_repo_id,
        )
        sys.exit(1)

    plat = _current_platform_key()
    repos: Dict[str, str] = {}
    for rid, entry in raw_repos.items():
        if not isinstance(entry, dict):
            logger.error("%s repositories.%s 不是 object", path, rid)
            sys.exit(1)
        paths = entry.get("paths") or {}
        abs_path = paths.get(plat)
        if not abs_path:
            logger.error(
                "%s repositories.%s 缺当前平台(%s)的路径", path, rid, plat,
            )
            sys.exit(1)
        # 路径在 JSON 里用 forward-slash 写,这里转成 os.sep 并取绝对
        repos[rid] = os.path.abspath(abs_path.replace("/", os.sep))

    logger.info(
        "[config] 加载 %d 个 repository(平台=%s,默认=%s): %s",
        len(repos), plat, default_repo_id, list(repos.keys()),
    )
    return repos, default_repo_id


class AppConfig:
    """应用配置类"""

    DATA_ROOT: str = os.path.abspath(_get_env("DATA_ROOT"))

    HOST: str = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8002"))

    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    FFPROBE_PATH: str = os.getenv("FFPROBE_PATH", "ffprobe")

    # ── Telegram "Saved Messages" 同步 ──────────────────────────────
    # 单文件 ≥ 此字节数 → 只下载封面/缩略图,不下载原文件,
    # 同时在 remote_media_reference 表记一行 source_url 供以后按需下载。
    TELEGRAM_LARGE_FILE_THRESHOLD: int = int(
        os.getenv("TELEGRAM_LARGE_FILE_THRESHOLD", str(50 * 1024 * 1024))
    )
    TELEGRAM_API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0") or "0")
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "").strip()
    # session / inbox 默认放 DATA_ROOT(机器本地,gitignored),不污染 backend 仓库
    # 留空让 get_telegram_session_path() / get_telegram_inbox_dir() 在解析时拼 DATA_ROOT,
    # 因为类体里没有 cls.DATA_ROOT
    TELEGRAM_SESSION_PATH: str = os.getenv("TELEGRAM_SESSION_PATH", "").strip()
    TELEGRAM_INBOX_DIR: str = os.getenv("TELEGRAM_INBOX_DIR", "").strip()
    TELEGRAM_POLL_INTERVAL: int = int(os.getenv("TELEGRAM_POLL_INTERVAL", "60"))

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

    # repositories.json 加载结果,模块加载时 eager 填充
    _REPOSITORIES: Dict[str, str] = {}
    _DEFAULT_REPO_ID: str = ""

    # DATA_ROOT 在 FastAPI 上的固定 URL 前缀(thumbs / actor_cover 都挂在这下面)
    DATA_URL_PREFIX: str = "/data"

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
        """{url_prefix: system_path}。

        - DATA_ROOT 永远挂在 `/data`(thumbs/actor_cover 子目录由前端拼)
        - 每个 repository 按 `/{repo_id}` 挂载,直接以 repo_id 小写作为 URL 段
        """
        mounts: Dict[str, str] = {cls.DATA_URL_PREFIX: cls.DATA_ROOT}
        for rid, abs_path in cls._REPOSITORIES.items():
            mounts[f"/{rid}"] = abs_path
        return mounts

    @classmethod
    def validate_repositories(cls) -> None:
        """启动时检查:repo_id 与 /data 不冲突。

        **不**强制检查 repo 路径是否实际存在 —— 缺失的路径在
        `app/__init__.py` 的 mount 循环里跳过(允许外接盘未挂时 backend 也能起来,
        对应 media URL 返回 404)。DATA_ROOT 本身的缺失在 mount 循环里 fail-fast。
        """
        if os.getenv("ALEMBIC_SKIP_REPO_LOAD") == "1":
            # alembic 上下文里 _REPOSITORIES 故意是空的,validate 也跳过
            return
        if not cls._REPOSITORIES:
            logger.error("repositories 为空,无法启动")
            sys.exit(1)
        if "data" in cls._REPOSITORIES:
            logger.error("repo_id 'data' 与内置 /data 静态前缀冲突,请改名")
            sys.exit(1)

    @classmethod
    def get_media_type(cls, file_path: str) -> str | None:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in cls.VIDEO_EXTENSIONS:
            return "VIDEO"
        elif ext in cls.IMAGE_EXTENSIONS:
            return "IMAGE"
        return None

    @classmethod
    def get_upload_root(cls) -> str:
        """default repo 的根目录(替代旧 UPLOAD_DIR 类属性的语义)。"""
        return cls._REPOSITORIES[cls._DEFAULT_REPO_ID]

    @classmethod
    def get_upload_dir(cls) -> str:
        """按日期分组的上传落地目录(default repo 之下)。"""
        from datetime import date
        today = date.today()
        return os.path.join(
            cls.get_upload_root(),
            str(today.year), f"{today.month:02d}", f"{today.day:02d}",
        )

    @classmethod
    def get_thumbs_dir(cls) -> str:
        # 与 Mac 端 (Models.swift localThumbURL) 一致:thumbs/preview/actor_cover
        # 都直接在 DATA_ROOT 根下,跟 `/data` URL mount 的根对齐
        # (`/data` → DATA_ROOT,所以 URL `/data/thumbs/x.webp` 物理就是 `DATA_ROOT/thumbs/x.webp`)。
        return os.path.join(cls.DATA_ROOT, "thumbs")

    @classmethod
    def get_thumbnail_path(cls, media_id: int) -> str:
        return os.path.join(cls.get_thumbs_dir(), f"{media_id}.webp")

    # ── Telegram 路径解析 ──────────────────────────────────────────
    @classmethod
    def get_telegram_session_path(cls) -> str:
        """Telethon session 文件绝对路径(默认 DATA_ROOT/.telegram.session)。"""
        return cls.TELEGRAM_SESSION_PATH or os.path.join(
            cls.DATA_ROOT, ".telegram.session"
        )

    @classmethod
    def get_telegram_inbox_dir(cls) -> str:
        """Telegram 媒体下载暂存目录(默认 DATA_ROOT/telegram_inbox/)。

        自动 mkdir。process_file() 之后会把文件 copy 进 uploads/YYYY/MM/DD/,
        inbox 文件本身不视为 repo(不被 register_relative 命中)。
        """
        d = cls.TELEGRAM_INBOX_DIR or os.path.join(cls.DATA_ROOT, "telegram_inbox")
        os.makedirs(d, exist_ok=True)
        return d

    # ── MP4 preview(为 GIF 等动画格式生成的小尺寸 H.264 视频)────
    # iOS MyNote 在 grid cell / 详情里优先用 AVPlayer 播这个文件
    # (VideoToolbox 硬件解码,<5ms 冷启),比 animated webp 快一个数量级。
    @classmethod
    def get_preview_dir(cls) -> str:
        return os.path.join(cls.DATA_ROOT, "preview")

    @classmethod
    def get_preview_path(cls, media_id: int) -> str:
        return os.path.join(cls.get_preview_dir(), f"{media_id}.mp4")

    @classmethod
    def get_actor_cover_dir(cls) -> str:
        return os.path.join(cls.DATA_ROOT, "actor_cover")

    @classmethod
    def get_actor_avatar_path(cls, actor_id: int) -> str:
        return os.path.join(cls.get_actor_cover_dir(), f"{actor_id}.webp")

    @classmethod
    def get_thumbnail_url(cls, media_id: int) -> str:
        return f"{cls.DATA_URL_PREFIX}/thumbs/{media_id}.webp"

    @classmethod
    def get_actor_avatar_url(cls, actor_id: int) -> str:
        return f"{cls.DATA_URL_PREFIX}/actor_cover/{actor_id}.webp"

    # ── 磁盘扫描缩略图(scan_thumbs/{fs_entry_id}.webp)────────────
    # 与 Media 的 thumbs/ 平级,直接在 DATA_ROOT 根下,所以同样由
    # `/data` 静态挂载自动 serve(`/data/scan_thumbs/x.webp` 物理对应
    # `DATA_ROOT/scan_thumbs/x.webp`),无需新挂载。
    # 目录由 scan_worker 首次写入前 os.makedirs 懒建,保持 config import 无副作用。
    @classmethod
    def get_scan_thumbs_dir(cls) -> str:
        return os.path.join(cls.DATA_ROOT, "scan_thumbs")

    @classmethod
    def get_scan_thumbnail_path(cls, fs_entry_id: int) -> str:
        return os.path.join(cls.get_scan_thumbs_dir(), f"{fs_entry_id}.webp")

    @classmethod
    def get_scan_thumbnail_url(cls, fs_entry_id: int) -> str:
        return f"{cls.DATA_URL_PREFIX}/scan_thumbs/{fs_entry_id}.webp"

    # ------------------------------------------------------------------ #
    # Repository API —— 把"挂载点"形式化到 DB 里(media.repo_id + 相对路径)
    # ------------------------------------------------------------------ #

    @classmethod
    def get_repositories(cls) -> Dict[str, str]:
        """{repo_id: 本机绝对路径}。"""
        return dict(cls._REPOSITORIES)

    @classmethod
    def default_repo_id(cls) -> str:
        return cls._DEFAULT_REPO_ID

    @classmethod
    def resolve_to_absolute(cls, repo_id: str, relative_path: str) -> Optional[str]:
        """(repo_id, relative_path) → 本机绝对路径。未知 repo 返回 None。

        relative_path 在 DB 里永远以 forward-slash 存储;这里转成 os.sep 再 join。
        单段相对路径(如 "x.mp4")也合法,直接落在 repo 根目录下。
        """
        if not repo_id:
            return None
        mount = cls._REPOSITORIES.get(repo_id)
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
        未命中 → ValueError。调用方对新上传文件应先 copy 进 default repo 再调用。
        """
        if not absolute_path:
            raise ValueError("Empty path")
        norm = absolute_path.replace("\\", "/")
        norm_lc = norm.lower()
        candidates = sorted(
            cls._REPOSITORIES.items(),
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
        """(repo_id, relative_path) → "/{repo_id}/relative/path" 的 HTTP URL。

        URL 段直接用 repo_id —— 跟 get_static_mounts() 一致。
        未知 repo 返回空串,由调用方决定兜底。
        """
        if not repo_id or repo_id not in cls._REPOSITORIES:
            return ""
        rel = (relative_path or "").lstrip("/")
        if not rel:
            return f"/{repo_id}"
        return f"/{repo_id}/{rel}"

    @classmethod
    def get_db_path(cls) -> str:
        return os.path.join(cls.DATA_ROOT, "db.sqlite3")


# 创建全局配置实例;模块加载时即把 repositories.json 读进类属性。
# 例外:alembic 的 env.py 会先 set ALEMBIC_SKIP_REPO_LOAD=1 再 import,
# 这样新机器从零跑 `alembic upgrade head` 时 seed migration 才能把 JSON 种出来。
# 真正的 API 进程不会带这个标志,启动后仍 fail-fast。
if os.getenv("ALEMBIC_SKIP_REPO_LOAD") != "1":
    AppConfig._REPOSITORIES, AppConfig._DEFAULT_REPO_ID = _load_repositories(AppConfig.DATA_ROOT)
config = AppConfig()
