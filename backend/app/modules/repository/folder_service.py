"""Maintain logical folders independently from messages."""
import os
import shutil
import uuid
from typing import BinaryIO, cast

from sqlalchemy.orm import Session

from app.config import config
from app.models import Folder, FolderLocation, RepositoryFile, RepositoryFolder


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
