"""HTTP boundary for repository catalog operations."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import get_db
from app.modules.repository.queries import browse, duplicate_files, list_repositories as query_repositories, summary
from app.modules.repository.schemas import DuplicateFileCursorResponse, DuplicateFileDeleteRequest, DuplicateFileDeleteResponse, RepositoryBrowseResponse, RepositorySummaryResponse

router = APIRouter(tags=["repositories"])


@router.get("/repositories", response_model=list[RepositorySummaryResponse])
def list_repositories(db: Session = Depends(get_db)):
    return query_repositories(db)


@router.get("/repositories/duplicate-files", response_model=DuplicateFileCursorResponse)
def list_duplicate_files(cursor: int | None = Query(None), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return duplicate_files(db, cursor, limit)


@router.delete("/repositories/duplicate-files/{media_id}", response_model=DuplicateFileDeleteResponse)
def remove_duplicate_files(media_id: int, payload: DuplicateFileDeleteRequest, db: Session = Depends(get_db)):
    from app.modules.repository.duplicate_file_service import delete_physical_files
    from app.shared.exceptions import ConflictError, NotFoundError, ValidationError
    try:
        return delete_physical_files(db, media_id, payload.repository_file_ids)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/repositories/{repo_id}", response_model=RepositorySummaryResponse)
def repository_detail(repo_id: str, db: Session = Depends(get_db)):
    try:
        return summary(db, repo_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/repositories/{repo_id}/browse", response_model=RepositoryBrowseResponse)
def browse_repository(repo_id: str, path: str = Query(""), db: Session = Depends(get_db)):
    try:
        return browse(db, repo_id, path)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/repositories/{repo_id}/scan")
def scan_repository(repo_id: str):
    from app.modules.repository import catalog as repository_catalog
    try:
        result = repository_catalog.rescan(repo_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Repository not found") from exc
    if result is None:
        raise HTTPException(status_code=409, detail="Scan already in progress")
    return result
