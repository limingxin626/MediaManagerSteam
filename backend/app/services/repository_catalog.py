"""Repository catalog scanner.

A scan records folders (including empty ones) and supported media files. Each
repository is swept independently and only after a complete traversal, so an
unmounted/offline or partially unreadable repository never loses catalog rows.
"""
import logging
import mimetypes
import os
import threading
from datetime import datetime
from pathlib import PurePosixPath
from typing import Optional

from app.config import config
from app.models import Media, Message, MessageFolder, RepositoryFile, RepositoryFolder, SessionLocal

logger = logging.getLogger(__name__)

_rescan_lock = threading.Lock()


def scan_media_type(path: str) -> Optional[str]:
    """Use the same format contract as Media materialization."""
    return config.get_media_type(path)


def scan_mime_type(path: str) -> str:
    mime = mimetypes.guess_type(path)[0]
    return mime or ("video/octet-stream" if scan_media_type(path) == "VIDEO" else "image/octet-stream")


def is_running() -> bool:
    return _rescan_lock.locked()


def _normalize_rel(path: str) -> str:
    path = path.replace("\\", "/").strip("/")
    return "" if path in ("", ".") else str(PurePosixPath(path))


def _filesystem_id(path: str) -> Optional[str]:
    try:
        stat = os.stat(path, follow_symlinks=False)
    except OSError:
        return None
    if not stat.st_ino:
        return None
    return f"{stat.st_dev}:{stat.st_ino}"


def _walk_repository(root: str, other_repo_roots: set[str]):
    """Return (folders, files, complete); complete=False suppresses sweep."""
    root = os.path.abspath(root)
    folders: list[tuple[str, str, Optional[str]]] = []
    files: list[tuple[str, str, int, float]] = []
    stack = [(root, "", "")]
    complete = True
    while stack:
        directory, directory_rel, directory_name = stack.pop()
        has_entries = False
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    has_entries = True
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            absolute = os.path.abspath(entry.path)
                            if os.path.normcase(absolute) in other_repo_roots:
                                continue
                            rel = _normalize_rel(os.path.relpath(absolute, root))
                            stack.append((absolute, rel, entry.name))
                        elif entry.is_file(follow_symlinks=False) and scan_media_type(entry.name):
                            stat = entry.stat(follow_symlinks=False)
                            rel = _normalize_rel(os.path.relpath(entry.path, root))
                            files.append((rel, entry.name, stat.st_size, stat.st_mtime))
                    except OSError as exc:
                        complete = False
                        logger.warning("[catalog] cannot inspect %s: %s", entry.path, exc)
        except OSError as exc:
            complete = False
            logger.warning("[catalog] cannot read directory %s: %s", directory, exc)
        if directory_rel == "" or has_entries:
            folders.append((directory_rel, directory_name, _filesystem_id(directory)))
    return folders, files, complete


def rescan(repo_id: Optional[str] = None) -> Optional[dict]:
    """Scan all repositories or one repository; return None on concurrent scan."""
    if not _rescan_lock.acquire(blocking=False):
        return None
    try:
        repos = config.get_repositories()
        if repo_id is not None and repo_id not in repos:
            raise KeyError(repo_id)
        selected = {repo_id: repos[repo_id]} if repo_id else repos
        roots = {os.path.normcase(os.path.abspath(path)) for path in repos.values()}
        totals = {"scanned": 0, "inserted": 0, "updated": 0, "unchanged": 0,
                  "deleted": 0, "matched": 0, "pending": 0, "offline": []}
        for rid, root in selected.items():
            result = _scan_repository(rid, root, roots - {os.path.normcase(os.path.abspath(root))})
            if result is None:
                totals["offline"].append(rid)
                continue
            for key in ("scanned", "inserted", "updated", "unchanged", "deleted", "matched", "pending"):
                totals[key] += result[key]
        from app.services import repository_materializer
        repository_materializer.wake()
        logger.info("[catalog] scan complete: %s", totals)
        return totals
    finally:
        _rescan_lock.release()


def _scan_repository(repo_id: str, root: str, other_roots: set[str]) -> Optional[dict]:
    if not os.path.isdir(root):
        logger.warning("[catalog] repository %s offline, preserving catalog: %s", repo_id, root)
        return None
    folders, files, complete = _walk_repository(root, other_roots)
    token = datetime.now()
    db = SessionLocal()
    inserted = updated = unchanged = matched = pending = 0
    try:
        folder_rows = db.query(RepositoryFolder).filter_by(repo_id=repo_id).all()
        existing_folders = {row.rel_path: row for row in folder_rows}
        folders_by_identity = {row.filesystem_id: row for row in folder_rows if row.filesystem_id}
        # Parents are always encountered before children after sorting by depth.
        for rel, name, filesystem_id in sorted(folders, key=lambda item: (item[0].count("/"), item[0])):
            row = folders_by_identity.get(filesystem_id) if filesystem_id else None
            if row is None:
                row = existing_folders.get(rel)
            parent_rel = _normalize_rel(str(PurePosixPath(rel).parent)) if rel else None
            parent = existing_folders.get(parent_rel) if parent_rel is not None else None
            if row is None:
                row = RepositoryFolder(repo_id=repo_id, filesystem_id=filesystem_id, rel_path=rel, name=name,
                                       parent_id=parent.id if parent else None, scanned_at=token)
                db.add(row)
                db.flush()
                existing_folders[rel] = row
                if filesystem_id:
                    folders_by_identity[filesystem_id] = row
                inserted += 1
            else:
                if row.rel_path != rel:
                    existing_folders.pop(row.rel_path, None)
                    existing_folders[rel] = row
                row.filesystem_id = filesystem_id
                row.rel_path = rel
                row.name = name
                row.parent_id = parent.id if parent else None
                row.scanned_at = token

        media_index = {(r.repo_id, r.file_path): r.id for r in db.query(Media).filter(Media.video_media_id.is_(None))}
        existing_files = {row.rel_path: row for row in db.query(RepositoryFile).filter_by(repo_id=repo_id)}
        for rel, name, size, mtime in files:
            folder_rel = _normalize_rel(str(PurePosixPath(rel).parent))
            folder = existing_folders[folder_rel]
            row = existing_files.get(rel)
            media_id = media_index.get((repo_id, rel))
            if row is None:
                row = RepositoryFile(repo_id=repo_id, folder_id=folder.id, rel_path=rel, name=name,
                    mime_type=scan_mime_type(rel), media_type=scan_media_type(rel), file_size=size,
                    mtime=mtime, scanned_at=token, media_id=media_id,
                    materialize_status="done" if media_id else "pending")
                db.add(row)
                inserted += 1
                matched += int(media_id is not None)
                pending += int(media_id is None)
            elif row.mtime != mtime or row.file_size != size:
                row.folder_id, row.name, row.file_size, row.mtime, row.scanned_at = folder.id, name, size, mtime, token
                row.mime_type, row.media_type = scan_mime_type(rel), scan_media_type(rel)
                # The path now points at different bytes. Never reattach the Media
                # formerly registered at this path; the worker hashes current content.
                row.media_id = None
                row.materialize_status = "pending"
                row.materialize_error = None
                row.is_hdr = None
                row.color_transfer = None
                updated += 1
                pending += 1
            else:
                row.folder_id = folder.id
                row.scanned_at = token
                if row.media_id is None:
                    if media_id is not None:
                        row.media_id, row.materialize_status, row.materialize_error = media_id, "done", None
                        matched += 1
                    elif row.materialize_status in ("done", "failed"):
                        # ON DELETE SET NULL preserves the row, and a new scan is an
                        # explicit retry signal for prior materialization failures.
                        row.materialize_status = "pending"
                        row.materialize_error = None
                        pending += 1
                unchanged += 1

        # SessionLocal uses autoflush=False; persist marks before querying stale rows.
        # Otherwise every existing row still looks stale on repeat scans.
        db.flush()
        deleted = 0
        removed_folder_message_ids: set[int] = set()
        if complete:
            stale_files = db.query(RepositoryFile).filter(
                RepositoryFile.repo_id == repo_id, RepositoryFile.scanned_at < token).all()
            deleted += len(stale_files)
            for row in stale_files:
                db.delete(row)
            stale_folders = db.query(RepositoryFolder).filter(
                RepositoryFolder.repo_id == repo_id, RepositoryFolder.scanned_at < token
            ).order_by(RepositoryFolder.rel_path.desc()).all()
            deleted += len(stale_folders)
            for row in stale_folders:
                if row.message_link is not None:
                    removed_folder_message_ids.add(row.message_link.message_id)
                db.delete(row)
        else:
            logger.warning("[catalog] repository %s scan incomplete; sweep skipped", repo_id)
        db.flush()
        for message_id in removed_folder_message_ids:
            if db.query(MessageFolder.id).filter_by(message_id=message_id).first() is None:
                message = db.get(Message, message_id)
                if message is not None:
                    db.delete(message)
        db.flush()
        from app.services.folder_message_service import ensure_folder_messages, reconcile_folder_messages
        message_ids = ensure_folder_messages(db, repo_id)
        reconcile_folder_messages(db, message_ids)
        db.commit()
        return {"scanned": len(folders) + len(files), "inserted": inserted, "updated": updated,
                "unchanged": unchanged, "deleted": deleted, "matched": matched, "pending": pending}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
