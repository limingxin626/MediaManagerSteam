"""Safe deletion of physical repository copies without deleting logical Media."""
import os
from pathlib import PurePosixPath, PureWindowsPath

from sqlalchemy.orm import Session

from app.config import config
from app.models import Media, RepositoryFile
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError
from app.shared.unit_of_work import commit


def _safe_repository_path(repo_id: str, rel_path: str) -> str:
    repositories = config.get_repositories()
    root = repositories.get(repo_id)
    if root is None:
        raise ValueError("Repository not found")
    if not rel_path or PurePosixPath(rel_path).is_absolute() or PureWindowsPath(rel_path).is_absolute():
        raise ValueError("Invalid repository path")
    normalized = rel_path.replace("\\", "/")
    if ".." in PurePosixPath(normalized).parts:
        raise ValueError("Repository path escapes root")

    root_real = os.path.realpath(root)
    candidate = os.path.realpath(os.path.join(root_real, *PurePosixPath(normalized).parts))
    try:
        if os.path.commonpath([root_real, candidate]) != root_real:
            raise ValueError("Repository path escapes root")
    except ValueError as exc:
        raise ValueError("Repository path escapes root") from exc
    if candidate == root_real:
        raise ValueError("Repository path is not a file")
    return candidate


def delete_physical_files(db: Session, media_id: int, repository_file_ids: list[int]) -> dict:
    if len(repository_file_ids) != len(set(repository_file_ids)):
        raise ValidationError("Duplicate repository file IDs")

    media = db.query(Media).filter(Media.id == media_id).first()
    if media is None:
        raise NotFoundError("Media not found")

    rows = db.query(RepositoryFile).filter(RepositoryFile.id.in_(repository_file_ids)).all()
    by_id = {row.id: row for row in rows}
    if len(by_id) != len(repository_file_ids):
        raise ConflictError("Repository file selection is stale")
    if any(row.media_id != media_id or row.materialize_status != "done" for row in rows):
        raise ValidationError("Repository files must be completed copies of this media")

    deleted_ids: list[int] = []
    missing_ids: list[int] = []
    failures: list[dict] = []
    removed_ids: set[int] = set()

    for file_id in repository_file_ids:
        row = by_id[file_id]
        try:
            absolute_path = _safe_repository_path(row.repo_id, row.rel_path)
            if os.path.lexists(absolute_path):
                if not os.path.isfile(absolute_path) or os.path.islink(absolute_path):
                    raise ValueError("Path is not a regular repository file")
                os.remove(absolute_path)
                deleted_ids.append(file_id)
            else:
                missing_ids.append(file_id)
            removed_ids.add(file_id)
        except (OSError, ValueError) as exc:
            failures.append({"id": file_id, "message": str(exc)})

    remaining = db.query(RepositoryFile).filter(
        RepositoryFile.media_id == media_id,
        RepositoryFile.materialize_status == "done",
        ~RepositoryFile.id.in_(removed_ids) if removed_ids else True,
    ).order_by(RepositoryFile.repo_id, RepositoryFile.rel_path, RepositoryFile.id).all()

    canonical_removed = any(
        row.id in removed_ids and row.repo_id == media.repo_id and row.rel_path == media.file_path
        for row in rows
    )
    if canonical_removed and remaining:
        media.repo_id = remaining[0].repo_id
        media.file_path = remaining[0].rel_path

    for row in rows:
        if row.id in removed_ids:
            db.delete(row)
    commit(db)

    canonical_available = any(
        row.repo_id == media.repo_id and row.rel_path == media.file_path
        for row in remaining
    )
    return {
        "deleted_ids": deleted_ids,
        "missing_ids": missing_ids,
        "failures": failures,
        "remaining_count": len(remaining),
        "canonical_available": canonical_available,
        "canonical_repo_id": media.repo_id,
        "canonical_file_path": media.file_path,
    }
