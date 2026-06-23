"""磁盘扫描后台 worker —— 逐个为 `fs_entry` 补 metadata + 缩略图。

进程内单 daemon 线程,在 `app/__init__.py` 末尾启动一次(api.py 是单进程 uvicorn,
模块只加载一次,所以恰好一个 worker)。

工作循环:轮询 `meta_status='pending' | thumb_status='pending'` 的行,逐行处理:
- 匹配到 Media 的行(`media_id` 非空):直接从 Media 行搬 metadata,复用其缩略图
  (置 reused),不读文件。video 额外一次 ffprobe 填 HDR(Media 无 HDR 列)。
- 未匹配的行:读文件抽 metadata(get_media_info)+ HDR + 生成 scan_thumb。

逐行 commit → grid 增量可见,崩溃最多丢一行。daemon 随进程退出(LAN 应用可接受,
在途行留 pending 下轮重试)。ffprobe/ffmpeg 是 subprocess、PIL IO 释放 GIL,
不阻塞 FastAPI 请求线程;WAL 让后台写与请求写并发。
"""
import logging
import os
import threading

from app.config import config
from app.models import SessionLocal, FsEntry, Media
from app.services import scan_service
from app.utils import MediaInfoUtils, ThumbnailUtils

logger = logging.getLogger(__name__)

_wake = threading.Event()
_started = False

# 从 Media 行 / get_media_info 搬到 fs_entry 的 metadata 列
_META_COLS = (
    "width", "height", "duration_ms", "fps", "bitrate",
    "video_codec", "audio_codec", "has_audio", "taken_at",
    "gps_lat", "gps_lng", "orientation", "camera_make", "camera_model", "lens",
)


def wake() -> None:
    """唤醒 worker 立即干活(rescan 末尾调用)。"""
    _wake.set()


def start_worker() -> None:
    """启动 worker(幂等)。在 app/__init__.py 末尾调用一次。"""
    global _started
    if _started:
        return
    _started = True

    # 注册 HEIC/HEIF 支持(PIL 需要);不可用则降级,HEIC 行缩略图会失败但不崩。
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        logger.info("[scan-worker] pillow-heif 已注册,HEIC 支持开启")
    except Exception:
        logger.warning("[scan-worker] pillow-heif 不可用,HEIC 缩略图/HDR 将不可用")

    threading.Thread(target=_run_loop, name="scan-worker", daemon=True).start()
    logger.info("[scan-worker] started")


def _run_loop() -> None:
    while True:
        try:
            n = _process_batch()
        except Exception:
            logger.exception("[scan-worker] batch 出错")
            n = 0
        if n == 0:
            # 无活:等唤醒,最多睡 5s 再轮询
            _wake.wait(timeout=5.0)
            _wake.clear()


def _process_batch() -> int:
    db = SessionLocal()
    try:
        rows = (
            db.query(FsEntry)
            .filter((FsEntry.meta_status == "pending") | (FsEntry.thumb_status == "pending"))
            .order_by(FsEntry.id.asc())
            .limit(50)
            .all()
        )
        for row in rows:
            try:
                _process_row(db, row)
            except Exception:
                logger.exception("[scan-worker] 行 %s 处理失败", row.id)
                row.meta_status = "failed"
                if row.thumb_status == "pending":
                    row.thumb_status = "failed"
            db.commit()  # 逐行 commit:grid 增量可见,崩溃最多丢一行
        return len(rows)
    finally:
        db.close()


def _process_row(db, row: FsEntry) -> None:
    abs_path = config.resolve_to_absolute(row.repo_id, row.rel_path)
    if not abs_path or not os.path.exists(abs_path):
        row.meta_status = "failed"
        row.thumb_status = "failed"
        return

    # ── reuse 分支:从匹配到的 Media 行搬 metadata,复用其缩略图 ──
    if row.media_id is not None:
        m = db.query(Media).filter(Media.id == row.media_id).first()
        if m is not None:
            for c in _META_COLS:
                setattr(row, c, getattr(m, c))
            if not row.mime_type:
                row.mime_type = m.mime_type
            # Media 没有 HDR 列,video 单独 probe 一次补上
            if row.media_type == "VIDEO":
                row.is_hdr, row.color_transfer = scan_service.probe_hdr(abs_path)
            row.meta_status = "reused"
            row.thumb_status = "reused"
            return
        # Media 已被删 → 清 media_id,落到读文件分支自己生成缩略图
        row.media_id = None

    # ── 读文件分支:抽 metadata + HDR + 生成 scan_thumb ──
    info = MediaInfoUtils.get_media_info(abs_path, row.media_type, config.FFPROBE_PATH)
    for k in _META_COLS:
        setattr(row, k, info.get(k))
    if row.media_type == "VIDEO":
        row.is_hdr, row.color_transfer = scan_service.probe_hdr(abs_path)
    else:
        row.is_hdr, row.color_transfer = scan_service.image_hdr_best_effort(abs_path)

    # 变更守卫:读文件期间文件若被改动(mtime 变),不存陈旧 metadata,
    # 重置 pending 留待下次 rescan(它会先更新 mtime)。
    try:
        if os.stat(abs_path).st_mtime != row.mtime:
            row.meta_status = "pending"
            row.thumb_status = "pending"
            return
    except OSError:
        pass

    row.meta_status = "done"

    os.makedirs(config.get_scan_thumbs_dir(), exist_ok=True)
    thumb_path = config.get_scan_thumbnail_path(row.id)
    ok = ThumbnailUtils.generate_thumbnail(
        abs_path, thumb_path, row.media_type, config.FFMPEG_PATH
    )
    row.thumb_status = "done" if ok else "failed"
