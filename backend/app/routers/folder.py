from datetime import datetime
from typing import cast

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.config import config
from app.models import Folder, FolderLocation, Media, RepositoryFile, Tag, folder_tag, get_db
from app.schemas.file import FileUploadResponse
from app.schemas.folder import (
    FolderCursorResponse,
    FolderDetailResponse,
    FolderLocationItem,
    FolderPreviewItem,
    FolderResponse,
    FolderTagCount,
    FolderTagItem,
)
from app.schemas.repositories import RepositoryFileResponse


router = APIRouter(prefix="/folders", tags=["folders"])


def _primary_location(folder: Folder):
    return next((location for location in folder.locations if location.role == "PRIMARY"), None)


def _load_folder_file_summaries(
    db: Session,
    folders: list[Folder],
) -> tuple[
    dict[int, int],
    dict[int, list[RepositoryFile]],
    dict[int, dict[str, RepositoryFile]],
]:
    """Load counts, previews and Kodi covers in a fixed number of queries."""
    logical_ids = [cast(int, folder.id) for folder in folders]
    if not logical_ids:
        return {}, {}, {}

    completed = (
        RepositoryFile.media_id.is_not(None),
        RepositoryFile.materialize_status == "done",
    )
    counts = {
        logical_id: count
        for logical_id, count in (
            db.query(
                FolderLocation.folder_id,
                func.count(func.distinct(RepositoryFile.media_id)),
            )
            .join(
                RepositoryFile,
                RepositoryFile.folder_id == FolderLocation.repository_folder_id,
            )
            .filter(FolderLocation.folder_id.in_(logical_ids), *completed)
            .group_by(FolderLocation.folder_id)
            .all()
        )
    }

    location_priority = case((FolderLocation.role == "PRIMARY", 0), else_=1)
    ranked_previews = (
        db.query(
            FolderLocation.folder_id.label("logical_folder_id"),
            RepositoryFile.id.label("repository_file_id"),
            func.row_number().over(
                partition_by=FolderLocation.folder_id,
                order_by=(
                    location_priority,
                    func.lower(RepositoryFile.name),
                    RepositoryFile.id,
                ),
            ).label("position"),
        )
        .join(
            RepositoryFile,
            RepositoryFile.folder_id == FolderLocation.repository_folder_id,
        )
        .filter(FolderLocation.folder_id.in_(logical_ids), *completed)
        .subquery()
    )
    preview_rows = (
        db.query(ranked_previews.c.logical_folder_id, RepositoryFile)
        .join(RepositoryFile, RepositoryFile.id == ranked_previews.c.repository_file_id)
        .options(joinedload(RepositoryFile.media))
        .filter(ranked_previews.c.position <= 4)
        .order_by(ranked_previews.c.logical_folder_id, ranked_previews.c.position)
        .all()
    )
    previews: dict[int, list[RepositoryFile]] = {}
    for logical_id, row in preview_rows:
        previews.setdefault(logical_id, []).append(row)

    cover_rows = (
        db.query(FolderLocation.folder_id, FolderLocation.role, RepositoryFile)
        .join(
            RepositoryFile,
            RepositoryFile.folder_id == FolderLocation.repository_folder_id,
        )
        .options(joinedload(RepositoryFile.media))
        .filter(
            FolderLocation.folder_id.in_(logical_ids),
            *completed,
            or_(
                func.lower(RepositoryFile.name).like("fanart.%"),
                func.lower(RepositoryFile.name).like("poster.%"),
            ),
        )
        .order_by(
            FolderLocation.folder_id,
            location_priority,
            FolderLocation.id,
            func.lower(RepositoryFile.name),
            RepositoryFile.id,
        )
        .all()
    )
    covers: dict[int, dict[str, RepositoryFile]] = {}
    for logical_id, _role, row in cover_rows:
        kind = row.name.rsplit(".", 1)[0].lower()
        if kind in {"fanart", "poster"}:
            covers.setdefault(logical_id, {}).setdefault(kind, row)

    return counts, previews, covers


def _folder_response(
    folder: Folder,
    counts: dict[int, int],
    previews: dict[int, list[RepositoryFile]],
    covers: dict[int, dict[str, RepositoryFile]],
) -> FolderResponse:
    primary = _primary_location(folder)
    physical = primary.repository_folder if primary is not None else None
    folder_id = cast(int, folder.id)
    preview_rows = previews.get(folder_id, [])
    folder_covers = covers.get(folder_id, {})
    fanart = folder_covers.get("fanart")
    poster = folder_covers.get("poster")
    return FolderResponse(
        id=cast(int, folder.id),
        name=cast(str, physical.name if physical is not None else ""),
        collection_id=cast(int | None, folder.collection_id),
        collection_name=folder.collection.name if folder.collection else None,
        issue_id=cast(int | None, folder.issue_id),
        issue_title=folder.issue.title if folder.issue else None,
        starred=bool(folder.starred),
        location_count=len(folder.locations),
        media_count=counts.get(folder_id, 0),
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


def _folder_preview_item(media: Media, name: str, source: str) -> FolderPreviewItem:
    return FolderPreviewItem(
        id=cast(int, media.id),
        repo_id=cast(str, media.repo_id),
        file_path=cast(str, media.file_path),
        name=name,
        mime_type=media.mime_type,
        width=media.width,
        height=media.height,
        duration_ms=media.duration_ms,
        video_media_id=media.video_media_id,
        frame_ms=media.frame_ms,
        start_ms=media.start_ms,
        end_ms=media.end_ms,
        source=source,
    )


def _folder_previews(
    db: Session,
    folder: Folder,
    files: list[RepositoryFile],
) -> list[FolderPreviewItem]:
    """Return Kodi preview images and preview children of videos in the folder."""
    primary = _primary_location(folder)
    primary_id = primary.repository_folder_id if primary is not None else None
    completed_files = [
        row for row in files
        if row.media is not None
        and row.media_id is not None
        and row.materialize_status == "done"
    ]
    named_rows = sorted(
        (
            row for row in completed_files
            if row.media_type == "IMAGE"
            and row.name.rsplit(".", 1)[0].lower().startswith(("preview", "preivew"))
        ),
        key=lambda row: (
            row.folder_id != primary_id,
            row.name.lower(),
            row.id,
        ),
    )

    result: list[FolderPreviewItem] = []
    seen_media_ids: set[int] = set()
    for row in named_rows:
        media_id = cast(int, row.media_id)
        if media_id in seen_media_ids:
            continue
        seen_media_ids.add(media_id)
        result.append(_folder_preview_item(row.media, row.name, "kodi"))

    child_rows = sorted(
        (row for row in completed_files if row.media.video_media_id is not None),
        key=lambda row: (
            row.folder_id != primary_id,
            row.media.video_media_id,
            row.media.frame_ms is None,
            row.media.frame_ms or 0,
            row.id,
        ),
    )
    for row in child_rows:
        media_id = cast(int, row.media_id)
        if media_id in seen_media_ids:
            continue
        seen_media_ids.add(media_id)
        result.append(_folder_preview_item(row.media, row.name, "video"))

    folder_media_ids = {cast(int, row.media_id) for row in completed_files}
    if not folder_media_ids:
        return result

    children = (
        db.query(Media)
        .filter(Media.video_media_id.in_(folder_media_ids))
        .order_by(
            Media.video_media_id,
            case((Media.frame_ms.is_(None), 1), else_=0),
            Media.frame_ms,
            Media.id,
        )
        .all()
    )
    for media in children:
        media_id = cast(int, media.id)
        if media_id in seen_media_ids:
            continue
        seen_media_ids.add(media_id)
        name = cast(str, media.file_path).replace("\\", "/").rsplit("/", 1)[-1]
        result.append(_folder_preview_item(media, name, "video"))
    return result


@router.get("", response_model=FolderCursorResponse)
def list_folders(
    cursor: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    starred: bool | None = Query(None),
    tag_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Folder).options(
        joinedload(Folder.collection),
        joinedload(Folder.issue),
        selectinload(Folder.locations).joinedload(FolderLocation.repository_folder),
        selectinload(Folder.tags),
    )
    if cursor is not None:
        query = query.filter(Folder.id < cursor)
    if starred is not None:
        query = query.filter(Folder.starred == (1 if starred else 0))
    if tag_id is not None:
        query = query.filter(Folder.tags.any(Tag.id == tag_id))
    rows = query.order_by(Folder.id.desc()).limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    counts, previews, covers = _load_folder_file_summaries(db, rows)
    return FolderCursorResponse(
        items=[_folder_response(folder, counts, previews, covers) for folder in rows],
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

    counts, previews, covers = _load_folder_file_summaries(db, [folder])
    base = _folder_response(folder, counts, previews, covers)
    locations = [
        FolderLocationItem(
            id=location.repository_folder.id,
            repo_id=location.repository_folder.repo_id,
            rel_path=location.repository_folder.rel_path,
            name=location.repository_folder.name,
            role=location.role,
            local_path=config.resolve_to_absolute(
                location.repository_folder.repo_id,
                location.repository_folder.rel_path,
            ),
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
        previews=_folder_previews(db, folder, files),
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
