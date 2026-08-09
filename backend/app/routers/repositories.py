"""Repository catalog browsing and refresh APIs."""
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.config import config
from app.models import Media, RepositoryFile, RepositoryFolder, get_db
from app.schemas.repositories import (
    DuplicateFileCursorResponse,
    DuplicateFileDeleteRequest,
    DuplicateFileDeleteResponse,
    DuplicateFileGroup,
    DuplicatePhysicalFileItem,
    RepositoryBrowseResponse,
    RepositoryFileResponse,
    RepositorySummaryResponse,
)

router = APIRouter(tags=["repositories"])


def _file_response(row: RepositoryFile) -> RepositoryFileResponse:
    response = RepositoryFileResponse.model_validate(row)
    media = row.media
    if media is not None:
        for field in (
            "width", "height", "duration_ms", "fps", "bitrate", "video_codec",
            "audio_codec", "has_audio", "taken_at", "gps_lat", "gps_lng",
            "orientation", "camera_make", "camera_model", "lens",
        ):
            setattr(response, field, getattr(media, field))
    return response


def _summary(db: Session, repo_id: str) -> RepositorySummaryResponse:
    repos = config.get_repositories()
    if repo_id not in repos:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositorySummaryResponse(
        repo_id=repo_id,
        root_path=repos[repo_id],
        online=os.path.isdir(repos[repo_id]),
        folder_count=db.query(func.count(RepositoryFolder.id)).filter_by(repo_id=repo_id).scalar() or 0,
        file_count=db.query(func.count(RepositoryFile.id)).filter_by(repo_id=repo_id).scalar() or 0,
        pending_count=db.query(func.count(RepositoryFile.id)).filter(
            RepositoryFile.repo_id == repo_id,
            RepositoryFile.materialize_status != "done",
        ).scalar() or 0,
    )


@router.get("/repositories", response_model=list[RepositorySummaryResponse])
def list_repositories(db: Session = Depends(get_db)):
    return [_summary(db, repo_id) for repo_id in config.get_repositories()]


@router.get("/repositories/duplicate-files", response_model=DuplicateFileCursorResponse)
def list_duplicate_files(
    cursor: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    duplicate_ids = (
        db.query(RepositoryFile.media_id.label("media_id"))
        .filter(
            RepositoryFile.media_id.is_not(None),
            RepositoryFile.materialize_status == "done",
        )
        .group_by(RepositoryFile.media_id)
        .having(func.count(RepositoryFile.id) > 1)
        .subquery()
    )
    media_query = db.query(Media).filter(
        Media.id.in_(db.query(duplicate_ids.c.media_id)),
        Media.video_media_id.is_(None),
    )
    if cursor is not None:
        media_query = media_query.filter(Media.id < cursor)
    media_rows = media_query.order_by(Media.id.desc()).limit(limit + 1).all()
    has_more = len(media_rows) > limit
    media_rows = media_rows[:limit]

    media_ids = [media.id for media in media_rows]
    files = []
    if media_ids:
        files = db.query(RepositoryFile).filter(
            RepositoryFile.media_id.in_(media_ids),
            RepositoryFile.materialize_status == "done",
        ).order_by(RepositoryFile.media_id, RepositoryFile.repo_id, RepositoryFile.rel_path).all()
    files_by_media: dict[int, list[RepositoryFile]] = {}
    for row in files:
        files_by_media.setdefault(row.media_id, []).append(row)

    items = []
    for media in media_rows:
        physical_files = [
            DuplicatePhysicalFileItem(
                id=row.id,
                repo_id=row.repo_id,
                rel_path=row.rel_path,
                local_file_path=config.resolve_to_absolute(row.repo_id, row.rel_path) or "",
                file_size=row.file_size,
                mtime=row.mtime,
                is_canonical=row.repo_id == media.repo_id and row.rel_path == media.file_path,
            )
            for row in files_by_media.get(media.id, [])
        ]
        items.append(DuplicateFileGroup(
            media_id=media.id,
            repo_id=media.repo_id,
            file_path=media.file_path,
            mime_type=media.mime_type,
            width=media.width,
            height=media.height,
            duration_ms=media.duration_ms,
            thumb_url=config.get_thumbnail_url(media.id),
            local_thumb_path=config.get_thumbnail_path(media.id),
            files=physical_files,
        ))
    return DuplicateFileCursorResponse(
        items=items,
        next_cursor=media_rows[-1].id if has_more and media_rows else None,
        has_more=has_more,
    )


@router.delete("/repositories/duplicate-files/{media_id}", response_model=DuplicateFileDeleteResponse)
def remove_duplicate_files(
    media_id: int,
    payload: DuplicateFileDeleteRequest,
    db: Session = Depends(get_db),
):
    from app.services.duplicate_file_service import delete_physical_files

    return delete_physical_files(db, media_id, payload.repository_file_ids)


@router.get("/repositories/{repo_id}", response_model=RepositorySummaryResponse)
def repository_detail(repo_id: str, db: Session = Depends(get_db)):
    return _summary(db, repo_id)


@router.get("/repositories/{repo_id}/browse", response_model=RepositoryBrowseResponse)
def browse_repository(repo_id: str, path: str = Query(""), db: Session = Depends(get_db)):
    path = path.replace("\\", "/").strip("/")
    summary = _summary(db, repo_id)
    folder = db.query(RepositoryFolder).filter_by(repo_id=repo_id, rel_path=path).first()
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    folders = db.query(RepositoryFolder).filter_by(
        repo_id=repo_id, parent_id=folder.id,
    ).order_by(func.lower(RepositoryFolder.name), RepositoryFolder.id).all()
    files = db.query(RepositoryFile).options(joinedload(RepositoryFile.media)).filter_by(
        repo_id=repo_id, folder_id=folder.id,
    ).order_by(func.lower(RepositoryFile.name), RepositoryFile.id).all()
    return RepositoryBrowseResponse(
        repository=summary,
        folder=folder,
        folders=folders,
        files=[_file_response(row) for row in files],
    )


@router.post("/repositories/{repo_id}/scan")
def scan_repository(repo_id: str):
    from app.services import repository_catalog

    try:
        result = repository_catalog.rescan(repo_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Repository not found")
    if result is None:
        raise HTTPException(status_code=409, detail="Scan already in progress")
    return result
