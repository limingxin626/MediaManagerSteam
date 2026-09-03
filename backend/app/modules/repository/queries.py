"""Repository catalog read models."""
import os

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.config import config
from app.models import Media, RepositoryFile, RepositoryFolder
from app.modules.repository.schemas import DuplicateFileCursorResponse, DuplicateFileGroup, DuplicatePhysicalFileItem, RepositoryBrowseResponse, RepositoryFileResponse, RepositorySummaryResponse


def file_response(row: RepositoryFile) -> RepositoryFileResponse:
    response = RepositoryFileResponse.model_validate(row)
    if row.media is not None:
        response.starred = bool(row.media.starred)
        for field in ("width", "height", "duration_ms", "fps", "bitrate", "video_codec", "audio_codec", "has_audio", "taken_at", "gps_lat", "gps_lng", "orientation", "camera_make", "camera_model", "lens"):
            setattr(response, field, getattr(row.media, field))
    return response


def summary(db, repo_id: str) -> RepositorySummaryResponse:
    repos = config.get_repositories()
    if repo_id not in repos:
        raise LookupError("Repository not found")
    return RepositorySummaryResponse(repo_id=repo_id, root_path=repos[repo_id], online=os.path.isdir(repos[repo_id]), folder_count=db.query(func.count(RepositoryFolder.id)).filter_by(repo_id=repo_id).scalar() or 0, file_count=db.query(func.count(RepositoryFile.id)).filter_by(repo_id=repo_id).scalar() or 0, pending_count=db.query(func.count(RepositoryFile.id)).filter(RepositoryFile.repo_id == repo_id, RepositoryFile.materialize_status != "done").scalar() or 0)


def list_repositories(db) -> list[RepositorySummaryResponse]:
    return [summary(db, repo_id) for repo_id in config.get_repositories()]


def duplicate_files(db, cursor=None, limit=20) -> DuplicateFileCursorResponse:
    duplicate_ids = db.query(RepositoryFile.media_id.label("media_id")).filter(RepositoryFile.media_id.is_not(None), RepositoryFile.materialize_status == "done").group_by(RepositoryFile.media_id).having(func.count(RepositoryFile.id) > 1).subquery()
    query = db.query(Media).filter(Media.id.in_(db.query(duplicate_ids.c.media_id)), Media.video_media_id.is_(None))
    if cursor is not None:
        query = query.filter(Media.id < cursor)
    media_rows = query.order_by(Media.id.desc()).limit(limit + 1).all()
    has_more, media_rows = len(media_rows) > limit, media_rows[:limit]
    ids = [media.id for media in media_rows]
    files = db.query(RepositoryFile).filter(RepositoryFile.media_id.in_(ids), RepositoryFile.materialize_status == "done").order_by(RepositoryFile.media_id, RepositoryFile.repo_id, RepositoryFile.rel_path).all() if ids else []
    by_media = {}
    for row in files:
        by_media.setdefault(row.media_id, []).append(row)
    items = []
    for media in media_rows:
        physical = [DuplicatePhysicalFileItem(id=row.id, repo_id=row.repo_id, rel_path=row.rel_path, local_file_path=config.resolve_to_absolute(row.repo_id, row.rel_path) or "", file_size=row.file_size, mtime=row.mtime, is_canonical=row.repo_id == media.repo_id and row.rel_path == media.file_path) for row in by_media.get(media.id, [])]
        items.append(DuplicateFileGroup(media_id=media.id, repo_id=media.repo_id, file_path=media.file_path, mime_type=media.mime_type, width=media.width, height=media.height, duration_ms=media.duration_ms, thumb_url=config.get_thumbnail_url(media.id), local_thumb_path=config.get_thumbnail_path(media.id), files=physical))
    return DuplicateFileCursorResponse(items=items, next_cursor=media_rows[-1].id if has_more and media_rows else None, has_more=has_more)


def browse(db, repo_id: str, path: str) -> RepositoryBrowseResponse:
    path = path.replace(chr(92), "/").strip("/")
    repository = summary(db, repo_id)
    folder = db.query(RepositoryFolder).filter_by(repo_id=repo_id, rel_path=path).first()
    if folder is None:
        raise LookupError("Folder not found")
    folders = db.query(RepositoryFolder).filter_by(repo_id=repo_id, parent_id=folder.id).order_by(func.lower(RepositoryFolder.name), RepositoryFolder.id).all()
    files = db.query(RepositoryFile).options(joinedload(RepositoryFile.media)).filter_by(repo_id=repo_id, folder_id=folder.id).order_by(func.lower(RepositoryFile.name), RepositoryFile.id).all()
    return RepositoryBrowseResponse(repository=repository, folder=folder, folders=folders, files=[file_response(row) for row in files])
