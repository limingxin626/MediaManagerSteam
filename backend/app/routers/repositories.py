"""Repository catalog browsing and refresh APIs."""
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.config import config
from app.models import RepositoryFile, RepositoryFolder, get_db
from app.schemas.repositories import (
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
