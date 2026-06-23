"""磁盘扫描服务 —— 把注册 repository 目录下的媒体文件索引到 `fs_entry` 表。

设计语义见 `app/models/fs_entry.py` 与计划文件。要点:
- `rescan()` 是手动触发的入口。只 `os.stat`(秒级,十万量级可接受),不读文件内容;
  metadata + 缩略图由 `scan_worker` 后台逐个补。
- mark-and-sweep:每次扫描用一个 `run_token`(datetime)写到每行 `scanned_at`,
  走完后删掉 `scanned_at < run_token` 的行(= 磁盘上已消失的文件)。
- 精确路径匹配 Media(不算 hash):命中则 `fs_entry.media_id` 记下,worker 直接
  从 Media 行搬 metadata 并复用其缩略图。
- 嵌套 repo:遍历时跳过本身是另一个 repo 根的子目录,避免同一文件出两行。
- 并发:模块级锁保证同一时刻只有一次 rescan;`scan_worker` 在 rescan 末尾被唤醒。
"""
import logging
import os
import threading
from datetime import datetime
from typing import Optional, Tuple

from app.config import config
from app.models import SessionLocal, FsEntry, Media
from app.utils import MediaInfoUtils

logger = logging.getLogger(__name__)

# ── 扫描专用扩展名集(比 config 的窄 Media 集更宽)────────────────
# 不改 config.VIDEO_EXTENSIONS/IMAGE_EXTENSIONS —— 那些驱动 Media import 去重管线。
SCAN_VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}
SCAN_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".heic", ".heif",
                   ".webp", ".bmp", ".tiff", ".tif"}
SCAN_EXTS = SCAN_VIDEO_EXTS | SCAN_IMAGE_EXTS

# HEIC/HEIF 等无 stdlib mimetypes 条目,这里兜底,保证返回非空 video/* | image/*
_SCAN_MIME_OVERRIDES = {
    ".heic": "image/heic", ".heif": "image/heif",
    ".mkv": "video/x-matroska", ".m4v": "video/x-m4v",
    ".mov": "video/quicktime", ".webm": "video/webm",
    ".avi": "video/x-msvideo", ".tiff": "image/tiff", ".tif": "image/tiff",
    ".bmp": "image/bmp", ".webp": "image/webp",
}

_BATCH = 1000

# 同一时刻只允许一次 rescan
_rescan_lock = threading.Lock()


def scan_media_type(path: str) -> Optional[str]:
    """返回 "VIDEO" / "IMAGE" / None —— 与 MediaInfoUtils.get_media_info /
    ThumbnailUtils.generate_thumbnail 期望的字面量一致。"""
    ext = os.path.splitext(path)[1].lower()
    if ext in SCAN_VIDEO_EXTS:
        return "VIDEO"
    if ext in SCAN_IMAGE_EXTS:
        return "IMAGE"
    return None


def scan_mime_type(path: str) -> str:
    """猜 mime,保证非空。HEIC 等用 override 兜底,再 fallback 到 octet-stream。"""
    import mimetypes
    ext = os.path.splitext(path)[1].lower()
    mime = _SCAN_MIME_OVERRIDES.get(ext) or mimetypes.guess_type(path)[0]
    if mime:
        return mime
    return "video/octet-stream" if scan_media_type(path) == "VIDEO" else "image/octet-stream"


def is_running() -> bool:
    """rescan 是否正在进行(供 /scan/status)。"""
    return _rescan_lock.locked()


# ── HDR 检测 ──────────────────────────────────────────────────────

def probe_hdr(abs_path: str) -> Tuple[Optional[int], Optional[str]]:
    """视频 HDR:读 video 流的 color_transfer。

    smpte2084(PQ/HDR10)/ arib-std-b67(HLG)→ is_hdr=1;其他 transfer → 0;
    无 video 流 / probe 失败 → (None, None)。
    复用 MediaInfoUtils._parse_ffprobe 的 -show_streams 输出(不额外多一次 ffprobe 类型)。
    """
    data = MediaInfoUtils._parse_ffprobe(abs_path, config.FFPROBE_PATH)
    if not data:
        return None, None
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            ct = s.get("color_transfer")
            return (1 if ct in ("smpte2084", "arib-std-b67") else 0), ct
    return None, None


def image_hdr_best_effort(abs_path: str) -> Tuple[Optional[int], Optional[str]]:
    """图片 HDR 尽力而为:仅 HEIC/HEIF 用 bit_depth>8 作 HDR 启发式。

    需要 pillow-heif;不可用或非 HEIC → (None, None)。JPEG/PNG gain-map HDR 本轮不检测。
    """
    ext = os.path.splitext(abs_path)[1].lower()
    if ext in (".heic", ".heif"):
        try:
            import pillow_heif
            heif = pillow_heif.read_heif(abs_path)
            bd = getattr(heif, "bit_depth", 8) or 8
            return (1 if bd > 8 else 0), (f"{bd}bit" if bd else None)
        except Exception:
            return None, None
    return None, None


# ── 遍历 ──────────────────────────────────────────────────────────

def _scandir_recursive(root: str, other_repo_roots: set):
    """迭代式递归遍历 root,yield (rel_path, size, mtime)。

    - 显式栈(非 os.walk),十万量级控内存。
    - entry.stat() 在 Windows 上 scandir 自带,免费;follow_symlinks=False 防环。
    - 跳过本身是另一个 repo 根的子目录(嵌套 repo 去重)。
    - 每 entry try/except,单个坏文件/目录不中断扫描。
    """
    root_norm = os.path.abspath(root)
    stack = [root_norm]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            # 跳过嵌套的其它 repo 根(它由那个 repo 自己收录)
                            if os.path.abspath(entry.path) in other_repo_roots:
                                continue
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            ext = os.path.splitext(entry.name)[1].lower()
                            if ext not in SCAN_EXTS:
                                continue
                            st = entry.stat()
                            rel = os.path.relpath(entry.path, root_norm).replace(os.sep, "/")
                            yield rel, st.st_size, st.st_mtime
                    except OSError:
                        continue
        except OSError:
            continue


# ── rescan 主流程 ─────────────────────────────────────────────────

def rescan() -> Optional[dict]:
    """全量增量扫描所有 repo。返回 counts dict;若已有 rescan 在跑,返回 None。"""
    if not _rescan_lock.acquire(blocking=False):
        return None
    try:
        return _rescan_locked()
    finally:
        _rescan_lock.release()


def _rescan_locked() -> dict:
    run_token = datetime.now()
    db = SessionLocal()
    try:
        repos = config.get_repositories()  # {repo_id: abs_root}
        all_roots = {os.path.abspath(p) for p in repos.values()}

        # 现有 fs_entry 行一次性载入内存:(repo_id, rel_path) → (id, mtime, file_size, media_id)
        existing: dict = {}
        for row in db.query(
            FsEntry.id, FsEntry.repo_id, FsEntry.rel_path,
            FsEntry.mtime, FsEntry.file_size, FsEntry.media_id,
        ).all():
            existing[(row.repo_id, row.rel_path)] = (row.id, row.mtime, row.file_size, row.media_id)

        # Media 匹配索引一次性载入:(repo_id, file_path) → media_id(排除视频预览帧)
        media_index: dict = {}
        for mid, mrepo, mpath in db.query(
            Media.id, Media.repo_id, Media.file_path
        ).filter(Media.video_media_id.is_(None)).all():
            media_index[(mrepo, mpath)] = mid

        insert_batch: list = []
        update_batch: list = []
        n_ins = n_upd = n_same = n_matched = n_pending = 0

        def _flush():
            if insert_batch:
                db.bulk_insert_mappings(FsEntry, insert_batch)
                insert_batch.clear()
            if update_batch:
                db.bulk_update_mappings(FsEntry, update_batch)
                update_batch.clear()
            db.commit()

        for repo_id, root in repos.items():
            if not os.path.isdir(root):
                logger.warning("[scan] repo %s 根目录不存在,跳过: %s", repo_id, root)
                continue
            other_roots = all_roots - {os.path.abspath(root)}
            for rel, size, mtime in _scandir_recursive(root, other_roots):
                key = (repo_id, rel)
                prev = existing.get(key)
                if prev is None:
                    # 新文件
                    media_id = media_index.get(key)
                    matched = media_id is not None
                    if matched:
                        n_matched += 1
                    else:
                        n_pending += 1
                    insert_batch.append({
                        "repo_id": repo_id,
                        "rel_path": rel,
                        "mime_type": scan_mime_type(rel),
                        "media_type": scan_media_type(rel),
                        "file_size": size,
                        "mtime": mtime,
                        "scanned_at": run_token,
                        "created_at": run_token,
                        "media_id": media_id,
                        "meta_status": "reused" if matched else "pending",
                        "thumb_status": "reused" if matched else "pending",
                    })
                    n_ins += 1
                else:
                    fid, old_mtime, old_size, old_media_id = prev
                    if old_mtime == mtime and old_size == size:
                        # 未变 —— 只刷新 scanned_at,不重新入队
                        update_batch.append({"id": fid, "scanned_at": run_token})
                        n_same += 1
                    else:
                        # 原地修改 —— 重算 media_id、重置状态、重新入队
                        media_id = media_index.get(key)
                        matched = media_id is not None
                        if matched:
                            n_matched += 1
                        else:
                            n_pending += 1
                        update_batch.append({
                            "id": fid,
                            "file_size": size,
                            "mtime": mtime,
                            "scanned_at": run_token,
                            "mime_type": scan_mime_type(rel),
                            "media_type": scan_media_type(rel),
                            "media_id": media_id,
                            "meta_status": "reused" if matched else "pending",
                            "thumb_status": "reused" if matched else "pending",
                        })
                        n_upd += 1

                if len(insert_batch) >= _BATCH or len(update_batch) >= _BATCH:
                    _flush()

        _flush()

        # ── sweep:删掉本轮没碰到的行(磁盘已消失)+ 清理它们自有的 scan_thumb ──
        stale = db.query(FsEntry.id, FsEntry.thumb_status).filter(
            FsEntry.scanned_at < run_token
        ).all()
        for r in stale:
            # reused 行指向 Media 缩略图,不拥有 scan_thumb;只删自有的
            if r.thumb_status in ("done", "pending", "failed"):
                p = config.get_scan_thumbnail_path(r.id)
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        stale_ids = [r.id for r in stale]
        for i in range(0, len(stale_ids), 500):
            chunk = stale_ids[i:i + 500]
            db.query(FsEntry).filter(FsEntry.id.in_(chunk)).delete(synchronize_session=False)
        db.commit()

        total = n_ins + n_upd + n_same
        result = {
            "scanned": total,
            "inserted": n_ins,
            "updated": n_upd,
            "unchanged": n_same,
            "deleted": len(stale_ids),
            "matched": n_matched,
            "pending": n_pending,
        }
        logger.info("[scan] rescan 完成: %s", result)
    finally:
        db.close()

    # 唤醒后台 worker 开始补 metadata / 缩略图(import 放这避免循环依赖)
    from app.services import scan_worker
    scan_worker.wake()
    return result
