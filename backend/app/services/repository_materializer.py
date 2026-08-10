"""Background materialization of catalog files into Media assets."""
import logging
import os
import threading

from app.config import config
from app.models import RepositoryFile, SessionLocal
from app.services import media_service

logger = logging.getLogger(__name__)
_wake = threading.Event()
_stop = threading.Event()
_thread: threading.Thread | None = None
_guard = threading.Lock()


def wake() -> None:
    _wake.set()


def start_worker() -> None:
    global _thread
    with _guard:
        if _thread is not None and _thread.is_alive():
            return
        _stop.clear()
        _thread = threading.Thread(target=_run_loop, name="catalog-materializer", daemon=True)
        _thread.start()
    logger.info("[catalog-worker] started")


def stop_worker() -> None:
    global _thread
    with _guard:
        thread = _thread
        if thread is None:
            return
        _stop.set()
        _wake.set()
    thread.join(timeout=10)
    with _guard:
        if _thread is thread:
            _thread = None
    logger.info("[catalog-worker] stopped")


def _run_loop() -> None:
    while not _stop.is_set():
        try:
            progress = _process_batch()
        except Exception:
            logger.exception("[catalog-worker] batch failed")
            progress = 0
        if progress == 0:
            _wake.wait(timeout=5)
            _wake.clear()


def _process_batch(limit: int = 20) -> int:
    db = SessionLocal()
    try:
        rows = db.query(RepositoryFile).filter(
            RepositoryFile.media_id.is_(None),
            RepositoryFile.materialize_status == "pending",
        ).order_by(RepositoryFile.id).limit(limit).all()
        progress = 0
        for row in rows:
            if _process_row(db, row):
                progress += 1
        return progress
    finally:
        db.close()


def _process_row(db, row: RepositoryFile) -> bool:
    """Materialize one row; return whether this pass reached a terminal state."""
    absolute = config.resolve_to_absolute(row.repo_id, row.rel_path)
    if not absolute or not os.path.isfile(absolute):
        row.materialize_status = "pending"
        row.materialize_error = "file unavailable"
        db.commit()
        return False

    expected_size, expected_mtime = row.file_size, row.mtime
    try:
        before = os.stat(absolute)
        if before.st_size != expected_size or before.st_mtime != expected_mtime:
            row.file_size = before.st_size
            row.mtime = before.st_mtime
            row.materialize_status = "pending"
            row.materialize_error = "file changed; awaiting stable retry"
            row.is_hdr = None
            row.color_transfer = None
            db.commit()
            return False

        result = media_service.process_file(db, absolute, commit=False)
        if result is None:
            row.materialize_status = "failed"
            row.materialize_error = "unsupported or unreadable media"
            db.commit()
            return True

        after = os.stat(absolute)
        if after.st_size != expected_size or after.st_mtime != expected_mtime:
            db.rollback()
            current = db.get(RepositoryFile, row.id)
            if current is not None:
                current.file_size = after.st_size
                current.mtime = after.st_mtime
                current.media_id = None
                current.materialize_status = "pending"
                current.materialize_error = "file changed during materialization"
                current.is_hdr = None
                current.color_transfer = None
                db.commit()
            return False

        media = result["media"]
        media_info = result.get("media_info") or {}
        canonical = config.resolve_to_absolute(media.repo_id, media.file_path)
        if not canonical or not os.path.isfile(canonical):
            media.repo_id = row.repo_id
            media.file_path = row.rel_path
        row.media_id = media.id
        row.materialize_status = "done"
        row.materialize_error = None
        row.is_hdr = media_info.get("is_hdr")
        row.color_transfer = media_info.get("color_transfer")
        db.flush()
        if row.folder.message_link is not None:
            from app.services.folder_message_service import reconcile_message_media
            reconcile_message_media(db, row.folder.message_link.message_id)
        db.commit()
        logger.info(
            "[catalog-worker] %s Media id=%s for %s",
            "created" if result["is_new"] else "reused", media.id, absolute,
        )
        return True
    except FileNotFoundError:
        db.rollback()
        current = db.get(RepositoryFile, row.id)
        if current is not None:
            current.materialize_status = "pending"
            current.materialize_error = "file unavailable"
            db.commit()
        return False
    except Exception as exc:
        db.rollback()
        current = db.get(RepositoryFile, row.id)
        if current is not None:
            current.materialize_status = "failed"
            current.materialize_error = str(exc)[:512]
            db.commit()
        logger.exception("[catalog-worker] failed to materialize %s", absolute)
        return True
