from datetime import datetime
from typing import cast

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.config import config
from app.models import Folder, FolderLocation, Media, RepositoryFile, Tag, folder_tag
from app.modules.repository.folder_classifier import (
    ClassifiedEntry,
    Detection,
    artwork_kind,
    classify_folder,
)
from app.modules.repository.folder_schemas import (
    FolderArtwork,
    FolderCursorResponse,
    FolderDetailResponse,
    FolderDetectionInfo,
    FolderLocationItem,
    FolderMediaEntry,
    FolderPreviewItem,
    FolderResponse,
    FolderTagCount,
    FolderTagItem,
)
from app.modules.repository.schemas import RepositoryFileResponse


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
            # 超集预筛:fanart/poster 及其标题前缀变体("MovieName-fanart.jpg")都含这些词。
            # 最终是否为封面由下方 artwork_kind() 决定(只取非编号的主封面)。
            or_(
                func.lower(RepositoryFile.name).like("%fanart%"),
                func.lower(RepositoryFile.name).like("%poster%"),
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
        kind = artwork_kind(row.name)
        # 主封面(非编号):fanart.jpg / poster.jpg / MovieName-fanart.jpg
        if kind is not None and kind[1] is None:
            covers.setdefault(logical_id, {}).setdefault(kind[0], row)

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
        kind=cast(str, folder.kind),
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
        response.starred = bool(row.media.starred)
        for field in (
            "width", "height", "duration_ms", "fps", "bitrate", "video_codec",
            "audio_codec", "has_audio", "taken_at", "gps_lat", "gps_lng",
            "orientation", "camera_make", "camera_model", "lens",
        ):
            setattr(response, field, getattr(row.media, field))
    return response


def _detection_response(detection: Detection) -> FolderDetectionInfo:
    return FolderDetectionInfo(
        source=detection.source,
        confidence=detection.confidence,
        reason=detection.reason,
        ambiguous=detection.ambiguous,
    )


def _entry_response(entry: ClassifiedEntry) -> FolderMediaEntry:
    return FolderMediaEntry(
        id=entry.id,
        kind=entry.kind,
        title=entry.title,
        sequence=entry.sequence,
        season_number=entry.season_number,
        episode_numbers=entry.episode_numbers,
        files=[_file_response(row) for row in entry.files],
        detection=_detection_response(entry.detection),
    )


def _folder_preview_item(media: Media, name: str, source: str) -> FolderPreviewItem:
    return FolderPreviewItem(
        id=cast(int, media.id),
        repo_id=cast(str, media.repo_id),
        file_path=cast(str, media.file_path),
        name=name,
        starred=bool(media.starred),
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
    def _is_named_kodi_preview(row: RepositoryFile) -> bool:
        """Kodi 风格的命名预览图:文件名以 preview/preivew 开头,
        或 fanart 的编号变体(fanart1.jpg / MovieName-fanart2.jpg)。"""
        if row.media_type != "IMAGE":
            return False
        lower = row.name.lower()
        if lower.startswith(("preview", "preivew")):
            return True
        kind = artwork_kind(row.name)
        return kind is not None and kind[0] == "fanart" and kind[1] is not None

    named_rows = sorted(
        (row for row in completed_files if _is_named_kodi_preview(row)),
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


def list_folders(
    db: Session,
    *,
    cursor: int | None = None,
    limit: int = 20,
    starred: bool | None = None,
    tag_id: int | None = None,
    kind: str | None = None,
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
    if kind:
        query = query.filter(Folder.kind == kind)
    rows = query.order_by(Folder.id.desc()).limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    counts, previews, covers = _load_folder_file_summaries(db, rows)
    return FolderCursorResponse(
        items=[_folder_response(folder, counts, previews, covers) for folder in rows],
        next_cursor=cast(int, rows[-1].id) if has_more and rows else None,
        has_more=has_more,
    )


def list_folder_tags(db: Session):
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


def get_folder(folder_id: int, db: Session):
    folder = db.get(Folder, folder_id)
    if folder is None:
        raise LookupError("Folder not found")

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
    primary = _primary_location(folder)
    classification = classify_folder(
        base.name,
        files,
        primary.repository_folder_id if primary is not None else None,
    )
    # Persist the freshly computed category so list filters (/folders?kind=) stay accurate.
    if folder.kind != classification.kind:
        folder.kind = classification.kind
        db.commit()
    payload = base.model_dump()
    payload["kind"] = classification.kind
    return FolderDetailResponse(
        **payload,
        artwork=FolderArtwork(poster=base.poster_file, fanart=base.fanart_file),
        entries=[_entry_response(entry) for entry in classification.entries],
        gallery=[_file_response(row) for row in classification.gallery],
        extras=[_entry_response(entry) for entry in classification.extras],
        unclassified=[_file_response(row) for row in classification.unclassified],
        primary_entry_id=classification.primary_entry_id,
        detection=_detection_response(classification.detection),
        locations=locations,
        files=[_file_response(row) for row in files],
        previews=_folder_previews(db, folder, files),
    )


