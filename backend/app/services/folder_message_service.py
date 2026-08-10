"""Materialize folder-backed messages from the repository catalog."""
import os
import shutil
import uuid
from collections import defaultdict
from datetime import datetime
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.models import Message, MessageFolder, MessageMedia, RepositoryFile, RepositoryFolder
from app.config import config


def _is_disposable_generated_message(message: Message) -> bool:
    return (
        not message.text
        and message.collection_id is None
        and message.issue_id is None
        and not message.starred
        and not message.tags
    )


def _folder_label(folder: RepositoryFolder) -> dict:
    return {"id": folder.id, "repo_id": folder.repo_id, "rel_path": folder.rel_path}


def bind_folder_to_existing_message(
    db: Session,
    message_id: int,
    folder_id: int,
) -> bool:
    """Explicitly bind one folder, replacing a disposable generated message."""
    message = db.get(Message, message_id)
    folder = db.get(RepositoryFolder, folder_id)
    if message is None:
        raise ValueError(f"Message not found: {message_id}")
    if folder is None or folder.rel_path == "":
        raise ValueError(f"Repository folder not found or is root: {folder_id}")

    link = folder.message_link
    if link is not None and link.message_id == message_id:
        return False
    old_message_id = link.message_id if link is not None else None
    has_primary = db.query(MessageFolder.id).filter_by(
        message_id=message_id,
        role="PRIMARY",
    ).first() is not None
    role = "MIRROR" if has_primary else "PRIMARY"
    if link is None:
        db.add(MessageFolder(
            message_id=message_id,
            repository_folder_id=folder_id,
            role=role,
        ))
    else:
        link.role = "MIRROR"
        db.flush()
        link.message_id = message_id
        link.role = role
    db.flush()
    reconcile_message_media(db, message_id)

    if old_message_id is not None:
        old_message = db.get(Message, old_message_id)
        if (
            old_message is not None
            and db.query(MessageFolder.id).filter_by(message_id=old_message_id).first() is None
            and _is_disposable_generated_message(old_message)
        ):
            db.delete(old_message)
            db.flush()
    return True


def backfill_existing_folder_messages(
    db: Session,
    apply: bool = False,
    sample_limit: int = 20,
) -> dict:
    """Bind folders to a unique existing message with the exact same media set."""
    folder_media: dict[int, frozenset[int]] = defaultdict(frozenset)
    media_by_folder: dict[int, set[int]] = defaultdict(set)
    completed_files = db.query(RepositoryFile).join(RepositoryFolder).filter(
        RepositoryFolder.rel_path != "",
        RepositoryFile.media_id.is_not(None),
        RepositoryFile.materialize_status == "done",
    ).all()
    for row in completed_files:
        media_by_folder[row.folder_id].add(row.media_id)
    folder_media = {
        folder_id: frozenset(media_ids)
        for folder_id, media_ids in media_by_folder.items()
        if media_ids
    }

    message_media: dict[int, set[int]] = defaultdict(set)
    for row in db.query(MessageMedia).all():
        message_media[row.message_id].add(row.media_id)
    messages_by_media: dict[frozenset[int], list[int]] = defaultdict(list)
    linked_message_ids = {row.message_id for row in db.query(MessageFolder).all()}
    for message_id, media_ids in message_media.items():
        if media_ids and message_id not in linked_message_ids:
            messages_by_media[frozenset(media_ids)].append(message_id)

    folders_by_media: dict[frozenset[int], list[int]] = defaultdict(list)
    for folder_id, media_ids in folder_media.items():
        folders_by_media[media_ids].append(folder_id)

    stats = {
        "candidate_folders": len(folder_media),
        "matched_folders": 0,
        "matched_messages": 0,
        "already_linked": 0,
        "ambiguous_folders": 0,
        "unmatched_folders": 0,
        "deleted_generated_messages": 0,
        "matches": [],
        "ambiguous": [],
        "unmatched": [],
    }

    for media_ids, folder_ids in sorted(folders_by_media.items(), key=lambda item: min(item[1])):
        candidate_message_ids = messages_by_media.get(media_ids, [])
        if len(candidate_message_ids) > 1:
            stats["ambiguous_folders"] += len(folder_ids)
            if len(stats["ambiguous"]) < sample_limit:
                stats["ambiguous"].append({
                    "folders": [_folder_label(db.get(RepositoryFolder, folder_id)) for folder_id in folder_ids],
                    "message_ids": candidate_message_ids,
                    "media_count": len(media_ids),
                })
            continue
        if not candidate_message_ids:
            linked = [
                folder_id for folder_id in folder_ids
                if db.get(RepositoryFolder, folder_id).message_link is not None
            ]
            stats["already_linked"] += len(linked)
            unmatched = [folder_id for folder_id in folder_ids if folder_id not in linked]
            stats["unmatched_folders"] += len(unmatched)
            if unmatched and len(stats["unmatched"]) < sample_limit:
                stats["unmatched"].append({
                    "folders": [_folder_label(db.get(RepositoryFolder, folder_id)) for folder_id in unmatched],
                    "media_count": len(media_ids),
                })
            continue

        target_message_id = candidate_message_ids[0]
        protected_links = []
        for folder_id in folder_ids:
            link = db.get(RepositoryFolder, folder_id).message_link
            if (
                link is not None
                and link.message_id != target_message_id
                and not _is_disposable_generated_message(link.message)
            ):
                protected_links.append(link.message_id)
        if protected_links:
            stats["ambiguous_folders"] += len(folder_ids)
            if len(stats["ambiguous"]) < sample_limit:
                stats["ambiguous"].append({
                    "folders": [_folder_label(db.get(RepositoryFolder, folder_id)) for folder_id in folder_ids],
                    "message_ids": candidate_message_ids,
                    "protected_link_message_ids": protected_links,
                    "media_count": len(media_ids),
                })
            continue

        stats["matched_messages"] += 1
        stats["matched_folders"] += len(folder_ids)
        if len(stats["matches"]) < sample_limit:
            stats["matches"].append({
                "folders": [_folder_label(db.get(RepositoryFolder, folder_id)) for folder_id in folder_ids],
                "message_id": target_message_id,
                "media_count": len(media_ids),
            })
        if not apply:
            continue

        old_message_ids: set[int] = set()
        for index, folder_id in enumerate(folder_ids):
            folder = db.get(RepositoryFolder, folder_id)
            link = folder.message_link
            role = "PRIMARY" if index == 0 else "MIRROR"
            if link is None:
                db.add(MessageFolder(
                    message_id=target_message_id,
                    repository_folder_id=folder_id,
                    role=role,
                ))
            else:
                old_message_ids.add(link.message_id)
                link.role = "MIRROR"
                db.flush()
                link.message_id = target_message_id
                link.role = role
            db.flush()

        reconcile_message_media(db, target_message_id)
        for old_message_id in old_message_ids - {target_message_id}:
            if db.query(MessageFolder.id).filter_by(message_id=old_message_id).first() is not None:
                continue
            old_message = db.get(Message, old_message_id)
            if old_message is not None and _is_disposable_generated_message(old_message):
                db.delete(old_message)
                stats["deleted_generated_messages"] += 1
        db.flush()

    return stats


def ensure_folder_messages(db: Session, repo_id: str) -> set[int]:
    """Create one independently backed message for each non-root folder."""
    folders = db.query(RepositoryFolder).filter(
        RepositoryFolder.repo_id == repo_id,
        RepositoryFolder.rel_path != "",
    ).all()
    message_ids: set[int] = set()
    for folder in folders:
        if folder.message_link is None:
            message = Message()
            db.add(message)
            db.flush()
            db.add(MessageFolder(
                message_id=message.id,
                repository_folder_id=folder.id,
                role="PRIMARY",
            ))
            message_ids.add(message.id)
        else:
            message_ids.add(folder.message_link.message_id)
    db.flush()
    return message_ids


def reconcile_message_media(db: Session, message_id: int) -> bool:
    """Replace the derived MessageMedia rows for one folder-backed message."""
    links = db.query(MessageFolder).filter_by(message_id=message_id).all()
    if not links:
        return False

    folder_ids = [link.repository_folder_id for link in links]
    rows = db.query(RepositoryFile).join(RepositoryFolder).filter(
        RepositoryFile.folder_id.in_(folder_ids),
        RepositoryFile.media_id.is_not(None),
        RepositoryFile.materialize_status == "done",
    ).order_by(
        RepositoryFolder.repo_id,
        RepositoryFolder.rel_path,
        RepositoryFile.name.collate("NOCASE"),
        RepositoryFile.id,
    ).all()

    media_ids = list(dict.fromkeys(row.media_id for row in rows))
    existing = db.query(MessageMedia).filter_by(message_id=message_id).order_by(MessageMedia.position).all()
    if [row.media_id for row in existing] == media_ids:
        return False

    for row in existing:
        db.delete(row)
    db.flush()
    for position, media_id in enumerate(media_ids):
        db.add(MessageMedia(message_id=message_id, media_id=media_id, position=position))

    message = db.get(Message, message_id)
    if message is not None:
        message.updated_at = datetime.now()
    db.flush()
    return True


def reconcile_folder_messages(db: Session, message_ids: set[int]) -> int:
    return sum(reconcile_message_media(db, message_id) for message_id in message_ids)


def store_file_in_primary_folder(
    db: Session,
    message_id: int,
    filename: str,
    source: BinaryIO,
) -> tuple[str, str]:
    """Atomically store an upload in a folder-backed message's primary folder."""
    link = db.query(MessageFolder).filter_by(message_id=message_id, role="PRIMARY").first()
    if link is None:
        raise ValueError("Message has no primary repository folder")
    if config.get_media_type(filename) is None:
        raise ValueError("Unsupported media file type")

    folder = link.folder
    directory = config.resolve_to_absolute(folder.repo_id, folder.rel_path)
    if directory is None or not os.path.isdir(directory):
        raise FileNotFoundError("Primary repository folder is unavailable")

    safe_name = os.path.basename(filename)
    stem, extension = os.path.splitext(safe_name)
    destination = os.path.join(directory, safe_name)
    counter = 1
    while os.path.exists(destination):
        destination = os.path.join(directory, f"{stem}_{counter}{extension}")
        counter += 1

    temporary = os.path.join(directory, f".uploading-{uuid.uuid4().hex}")
    try:
        with open(temporary, "wb") as output:
            shutil.copyfileobj(source, output)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
    return folder.repo_id, destination