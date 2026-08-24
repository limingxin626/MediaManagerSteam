from datetime import datetime
from typing import cast

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import Folder, RepositoryFile, Tag, folder_tag, get_db
from app.schemas.file import FileUploadResponse
from app.schemas.folder import (
    FolderCursorResponse,
    FolderDetailResponse,
    FolderLocationItem,
    FolderResponse,
    FolderTagCount,
    FolderTagItem,
)
from app.schemas.repositories import RepositoryFileResponse


router = APIRouter(prefix="/folders", tags=["folders"])


def _primary_location(folder: Folder):
    return next((location for location in folder.locations if location.role == "PRIMARY"), None)


def _folder_response(db: Session, folder: Folder) -> FolderResponse:
    primary = _primary_location(folder)
    physical = primary.repository_folder if primary is not None else None
    physical_ids = [location.repository_folder_id for location in folder.locations]
    media_count = 0
    if physical_ids:
        media_count = db.query(func.count(func.distinct(RepositoryFile.media_id))).filter(
            RepositoryFile.folder_id.in_(physical_ids),
            RepositoryFile.media_id.is_not(None),
            RepositoryFile.materialize_status == "done",
        ).scalar() or 0
    preview_rows = []
    cover_rows = []
    if physical_ids:
        files_query = db.query(RepositoryFile).options(joinedload(RepositoryFile.media)).filter(
            RepositoryFile.folder_id.in_(physical_ids),
            RepositoryFile.media_id.is_not(None),
            RepositoryFile.materialize_status == "done",
        )
        preview_rows = files_query.order_by(func.lower(RepositoryFile.name), RepositoryFile.id).limit(4).all()
        cover_rows = files_query.filter(or_(
            func.lower(RepositoryFile.name).like("fanart.%"),
            func.lower(RepositoryFile.name).like("poster.%"),
        )).order_by(func.lower(RepositoryFile.name), RepositoryFile.id).all()
    fanart = next((row for row in cover_rows if row.name.rsplit(".", 1)[0].lower() == "fanart"), None)
    poster = next((row for row in cover_rows if row.name.rsplit(".", 1)[0].lower() == "poster"), None)
    return FolderResponse(
        id=cast(int, folder.id),
        name=cast(str, physical.name if physical is not None else ""),
        collection_id=cast(int | None, folder.collection_id),
        collection_name=folder.collection.name if folder.collection else None,
        issue_id=cast(int | None, folder.issue_id),
        issue_title=folder.issue.title if folder.issue else None,
        starred=bool(folder.starred),
        location_count=len(folder.locations),
        media_count=media_count,
        primary_repo_id=physical.repo_id if physical is not None else None,
        primary_folder_path=physical.rel_path if physical is not None else None,
        tags=[FolderTagItem(id=tag.id, name=tag.name, category=tag.category) for tag in folder.tags],
        preview_files=[_file_response(row) for row in preview_rows],
        fanart_file=_file_response(fanart) if fanart is not None else None,
        poster_file=_file_response(poster) if poster is not None else None,
        created_at=cast(datetime, folder.created_at).isoformat(),
        updated_at=cast(datetime, folder.updated_at).isoformat(),
    )


def _file_response(row: RepositoryFile) -> RepositoryFileResponse:
    response = RepositoryFileResponse.model_validate(row)
    if row.media is not None:
        for field in (
            "width", "height", "duration_ms", "fps", "bitrate", "video_codec",
            "audio_codec", "has_audio", "taken_at", "gps_lat", "gps_lng",
            "orientation", "camera_make", "camera_model", "lens",
        ):
            setattr(response, field, getattr(row.media, field))
    return response


@router.get("", response_model=FolderCursorResponse)
def list_folders(
    cursor: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    starred: bool | None = Query(None),
    tag_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Folder)
    if cursor is not None:
        query = query.filter(Folder.id < cursor)
    if starred is not None:
        query = query.filter(Folder.starred == (1 if starred else 0))
    if tag_id is not None:
        query = query.filter(Folder.tags.any(Tag.id == tag_id))
    rows = query.order_by(Folder.id.desc()).limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    return FolderCursorResponse(
        items=[_folder_response(db, folder) for folder in rows],
        next_cursor=cast(int, rows[-1].id) if has_more and rows else None,
        has_more=has_more,
    )


@router.get("/tags", response_model=list[FolderTagCount])
def list_folder_tags(db: Session = Depends(get_db)):
    rows = (
        db.query(Tag, func.count(folder_tag.c.folder_id).label("folder_count"))
        .join(folder_tag, folder_tag.c.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(func.count(folder_tag.c.folder_id).desc(), func.lower(Tag.name))
        .all()
    )
    return [
        FolderTagCount(
            id=tag.id,
            name=tag.name,
            category=tag.category,
            folder_count=folder_count,
        )
        for tag, folder_count in rows
    ]


@router.get("/{folder_id}", response_model=FolderDetailResponse)
def get_folder(folder_id: int, db: Session = Depends(get_db)):
    folder = db.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")

    base = _folder_response(db, folder)
    locations = [
        FolderLocationItem(
            id=location.repository_folder.id,
            repo_id=location.repository_folder.repo_id,
            rel_path=location.repository_folder.rel_path,
            name=location.repository_folder.name,
            role=location.role,
        )
        for location in sorted(folder.locations, key=lambda item: (item.role != "PRIMARY", item.id))
    ]
    physical_ids = [location.repository_folder_id for location in folder.locations]
    files = []
    if physical_ids:
        files = db.query(RepositoryFile).options(joinedload(RepositoryFile.media)).filter(
            RepositoryFile.folder_id.in_(physical_ids),
        ).order_by(func.lower(RepositoryFile.name), RepositoryFile.id).all()
    return FolderDetailResponse(
        **base.model_dump(),
        locations=locations,
        files=[_file_response(row) for row in files],
    )


@router.post("/{folder_id}/files", response_model=FileUploadResponse, status_code=202)
async def upload_file_to_folder(
    folder_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    from app.services import repository_catalog
    from app.services.folder_service import store_file_in_primary_folder

    try:
        repo_id, destination = store_file_in_primary_folder(
            db,
            folder_id,
            file.filename or "",
            file.file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    finally:
        await file.close()

    repository_catalog.rescan(repo_id)
    return FileUploadResponse(message="上传成功，等待媒体处理", path=destination)