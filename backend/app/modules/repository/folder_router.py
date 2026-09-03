"""HTTP boundary for logical repository folders."""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.models import get_db
from app.modules.repository.file_schemas import FileUploadResponse
from app.modules.repository.folder_queries import get_folder as query_folder
from app.modules.repository.folder_queries import list_folder_tags as query_folder_tags
from app.modules.repository.folder_queries import list_folders as query_folders
from app.modules.repository.folder_schemas import (
    FolderCursorResponse,
    FolderDetailResponse,
    FolderTagCount,
)

router = APIRouter(prefix="/folders", tags=["folders"])


@router.get("", response_model=FolderCursorResponse)
def list_folders(cursor: int | None = Query(None), limit: int = Query(20, ge=1, le=100), starred: bool | None = Query(None), tag_id: int | None = Query(None), db: Session = Depends(get_db)):
    return query_folders(db, cursor=cursor, limit=limit, starred=starred, tag_id=tag_id)


@router.get("/tags", response_model=list[FolderTagCount])
def list_folder_tags(db: Session = Depends(get_db)):
    return query_folder_tags(db)


@router.get("/{folder_id}", response_model=FolderDetailResponse)
def get_folder(folder_id: int, db: Session = Depends(get_db)):
    try:
        return query_folder(folder_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{folder_id}/files", response_model=FileUploadResponse, status_code=202)
async def upload_file_to_folder(folder_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    from app.modules.repository import catalog as repository_catalog
    from app.modules.repository.folder_service import store_file_in_primary_folder
    try:
        repo_id, destination = store_file_in_primary_folder(db, folder_id, file.filename or "", file.file)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        await file.close()
    repository_catalog.rescan(repo_id)
    return FileUploadResponse(message="上传成功，等待媒体处理", path=destination)
