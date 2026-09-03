"""Maintain logical folders independently from messages."""
import os
import shutil
import uuid
from collections import defaultdict
from typing import BinaryIO, cast

from sqlalchemy.orm import Session

from app.config import config
from app.models import Folder, FolderLocation, RepositoryFile, RepositoryFolder
from app.modules.repository.folder_classifier import FolderClassification, classify_folder


def _primary_location(folder: Folder) -> FolderLocation | None:
    return next((location for location in folder.locations if location.role == "PRIMARY"), None)


def classify_logical_folder(db: Session, folder: Folder) -> FolderClassification:
    """Run the classifier over a logical folder's catalogued files and return the result.

    The caller decides whether/how to persist ``folder.kind``.
    """
    primary = _primary_location(folder)
    physical = primary.repository_folder if primary is not None else None
    name = physical.name if physical is not None else ""
    physical_ids = [location.repository_folder_id for location in folder.locations]
    files: list[RepositoryFile] = []
    if physical_ids:
        files = db.query(RepositoryFile).filter(RepositoryFile.folder_id.in_(physical_ids)).all()
    primary_folder_id = physical.id if physical is not None else None
    return classify_folder(name, files, primary_folder_id)


def refresh_folder_kind(db: Session, folder: Folder) -> str:
    """Recompute and persist ``folder.kind``; returns the resulting kind string."""
    classification = classify_logical_folder(db, folder)
    folder.kind = classification.kind
    return classification.kind


def refresh_repository_folder_kinds(db: Session, repo_id: str) -> int:
    """Reclassify and persist kind for every logical folder rooted in ``repo_id``.

    Batches file loading (one query per repo, no per-folder N+1). The linkage to
    the logical ``Folder`` is resolved with a SQL join rather than the
    ``RepositoryFolder.folder_location`` relationship attribute, which can hold a
    stale ``None`` right after ``ensure_folders`` creates the link in the same
    session. Returns the number of logical folders refreshed. Caller commits.
    """
    links = (
        db.query(RepositoryFolder, FolderLocation)
        .join(FolderLocation, FolderLocation.repository_folder_id == RepositoryFolder.id)
        .filter(RepositoryFolder.repo_id == repo_id)
        .all()
    )
    by_logical: dict[int, list[tuple[RepositoryFolder, str]]] = defaultdict(list)
    for physical, location in links:
        by_logical[location.folder_id].append((physical, location.role))
    if not by_logical:
        return 0

    physical_ids = [physical.id for items in by_logical.values() for physical, _ in items]
    files_by_physical: dict[int, list[RepositoryFile]] = defaultdict(list)
    for file_row in db.query(RepositoryFile).filter(RepositoryFile.folder_id.in_(physical_ids)):
        files_by_physical[file_row.folder_id].append(file_row)

    refreshed = 0
    for folder_id, members in by_logical.items():
        folder = db.get(Folder, folder_id)
        if folder is None:
            continue
        # Prefer the PRIMARY location (unique per logical folder); else first by id.
        members.sort(key=lambda item: (item[1] != "PRIMARY", item[0].id))
        primary = members[0][0]
        files: list[RepositoryFile] = []
        for physical, _role in members:
            files.extend(files_by_physical.get(physical.id, ()))
        classification = classify_folder(primary.name, files, primary.id)
        folder.kind = classification.kind
        refreshed += 1
    return refreshed


def refresh_kind_for_repository_folder(db: Session, repository_folder_id: int) -> bool:
    """Refresh the kind of the logical folder that owns ``repository_folder_id``.

    Used after a single file materializes so a folder's category stays accurate
    without a full reclassification pass. Returns whether a logical folder changed.
    """
    location = (
        db.query(FolderLocation)
        .filter_by(repository_folder_id=repository_folder_id)
        .first()
    )
    if location is None:
        return False
    folder = db.get(Folder, location.folder_id)
    if folder is None:
        return False
    refresh_folder_kind(db, folder)
    return True


def _has_user_metadata(folder: Folder) -> bool:
    return bool(
        folder.collection_id is not None
        or folder.issue_id is not None
        or folder.starred
        or folder.tags
    )


def ensure_folders(db: Session, repo_id: str) -> set[int]:
    physical_folders = db.query(RepositoryFolder).filter(
        RepositoryFolder.repo_id == repo_id,
        RepositoryFolder.rel_path != "",
    ).all()
    folder_ids: set[int] = set()

    for physical in physical_folders:
        has_files = db.query(RepositoryFile.id).filter_by(folder_id=physical.id).first() is not None
        location = physical.folder_location
        if not has_files:
            if location is not None and not _has_user_metadata(location.folder):
                logical = location.folder
                db.delete(location)
                db.flush()
                if not logical.locations:
                    db.delete(logical)
                else:
                    primary = next((item for item in logical.locations if item.role == "PRIMARY"), None)
                    if primary is None:
                        logical.locations[0].role = "PRIMARY"
            continue

        if location is None:
            logical = Folder(created_at=physical.created_at, updated_at=physical.updated_at)
            db.add(logical)
            db.flush()
            db.add(FolderLocation(
                folder_id=logical.id,
                repository_folder_id=physical.id,
                role="PRIMARY",
            ))
            folder_ids.add(cast(int, logical.id))
        else:
            folder_ids.add(cast(int, location.folder_id))

    db.flush()
    orphaned = db.query(Folder).filter(~Folder.locations.any()).all()
    for logical in orphaned:
        if not _has_user_metadata(logical):
            db.delete(logical)
    db.flush()
    return folder_ids


def store_file_in_primary_folder(
    db: Session,
    folder_id: int,
    filename: str,
    source: BinaryIO,
) -> tuple[str, str]:
    location = db.query(FolderLocation).filter_by(folder_id=folder_id, role="PRIMARY").first()
    if location is None:
        raise ValueError("Folder has no primary repository location")
    if config.get_media_type(filename) is None:
        raise ValueError("Unsupported media file type")

    physical = location.repository_folder
    directory = config.resolve_to_absolute(physical.repo_id, physical.rel_path)
    if directory is None or not os.path.isdir(directory):
        raise FileNotFoundError("Primary repository folder is unavailable")

    safe_name = os.path.basename(filename)
    stem, extension = os.path.splitext(safe_name)
    destination = os.path.join(directory, safe_name)
    counter = 1
    while os.path.exists(destination):
        destination = os.path.join(directory, f"{stem}_{counter}{extension}")
        counter += 1

    temporary = os.path.join(directory, f".{uuid.uuid4().hex}.upload")
    try:
        with open(temporary, "wb") as output:
            shutil.copyfileobj(source, output)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
    return physical.repo_id, destination
