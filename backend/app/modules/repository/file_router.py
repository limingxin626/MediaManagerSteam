"""HTTP boundary for filesystem operations."""

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.modules.repository import file_service
from app.modules.repository.file_schemas import (
    FileListResponse,
    FileOperationResponse,
    FileUploadResponse,
)

router = APIRouter(prefix="/files", tags=["files"])


def _translate_file_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, (FileExistsError, ValueError)):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/list", response_model=FileListResponse, summary="列出配置根目录下的文件和文件夹"
)
def list_path(root_id: str, path: Optional[str] = ""):
    try:
        return file_service.list_path(root_id, path or "")
    except Exception as exc:
        raise _translate_file_error(exc) from exc


@router.delete(
    "/delete", response_model=FileOperationResponse, summary="删除文件或文件夹"
)
def delete_path(root_id: str, path: str):
    try:
        return file_service.delete_path(root_id, path)
    except Exception as exc:
        raise _translate_file_error(exc) from exc


@router.post("/move", response_model=FileOperationResponse, summary="移动文件或文件夹")
def move_path(root_id: str, source_path: str, destination_path: str):
    try:
        return file_service.move_path(root_id, source_path, destination_path)
    except Exception as exc:
        raise _translate_file_error(exc) from exc


@router.put(
    "/rename", response_model=FileOperationResponse, summary="重命名文件或文件夹"
)
def rename_path(root_id: str, path: str, new_name: str):
    try:
        return file_service.rename_path(root_id, path, new_name)
    except Exception as exc:
        raise _translate_file_error(exc) from exc


@router.post(
    "/create", response_model=FileOperationResponse, summary="创建文件或文件夹"
)
def create_path(root_id: str, path: str, type: str):
    try:
        return file_service.create_path(root_id, path, type)
    except Exception as exc:
        raise _translate_file_error(exc) from exc


@router.post("/upload", response_model=FileUploadResponse, summary="上传文件")
async def upload_file(
    file: UploadFile = File(...), root_id: str = Form(...), path: str = Form("")
):
    try:
        return file_service.upload_file(
            file.file, file.filename or "upload", root_id, path
        )
    except Exception as exc:
        raise _translate_file_error(exc) from exc
    finally:
        await file.close()


@router.post(
    "/upload-media",
    response_model=FileUploadResponse,
    status_code=201,
    summary="上传媒体文件",
)
async def upload_media(file: UploadFile = File(...)):
    try:
        return file_service.upload_media(file.file, file.filename or "")
    except Exception as exc:
        raise _translate_file_error(exc) from exc
    finally:
        await file.close()
