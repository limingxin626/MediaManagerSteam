"""Sandboxed filesystem use cases for configured data and repository roots."""
from __future__ import annotations

import os
import shutil
import time
import uuid
from pathlib import PurePosixPath, PureWindowsPath
from typing import BinaryIO

from app.config import AppConfig, get_settings
from app.modules.repository.file_schemas import FileInfo, FileListResponse, FileOperationResponse, FileUploadResponse


class UnsafePathError(ValueError):
    """A requested path is outside its configured filesystem capability."""


def roots(settings: AppConfig | None = None) -> dict[str, str]:
    settings = settings or get_settings()
    return {"data": settings.DATA_ROOT, **settings.get_repositories()}


def resolve_path(root_id: str, relative_path: str = "", *, settings: AppConfig | None = None, allow_root: bool = True) -> str:
    root = roots(settings).get(root_id)
    if root is None:
        raise UnsafePathError("未知的文件根目录")
    path = (relative_path or "").replace(chr(92), "/")
    if PurePosixPath(path).is_absolute() or PureWindowsPath(path).is_absolute():
        raise UnsafePathError("只允许根目录内的相对路径")
    parts = PurePosixPath(path).parts
    if ".." in parts:
        raise UnsafePathError("路径不能离开根目录")
    root_real = os.path.realpath(root)
    candidate = os.path.realpath(os.path.join(root_real, *parts))
    try:
        inside = os.path.commonpath((root_real, candidate)) == root_real
    except ValueError:
        inside = False
    if not inside or (not allow_root and candidate == root_real):
        raise UnsafePathError("路径不能离开或指向根目录")
    return candidate


def _relative(root_id: str, absolute_path: str, settings: AppConfig | None = None) -> str:
    return os.path.relpath(absolute_path, roots(settings)[root_id]).replace(chr(92), "/").removeprefix("./")


def list_path(root_id: str, path: str = "", settings: AppConfig | None = None) -> FileListResponse:
    absolute = resolve_path(root_id, path, settings=settings)
    if not os.path.isdir(absolute):
        raise FileNotFoundError("目录不存在")
    items = []
    with os.scandir(absolute) as entries:
        for entry in entries:
            if entry.is_symlink():
                continue
            stat = entry.stat(follow_symlinks=False)
            items.append(FileInfo(name=entry.name, path=_relative(root_id, entry.path, settings), type="directory" if entry.is_dir(follow_symlinks=False) else "file", size=stat.st_size if entry.is_file(follow_symlinks=False) else None, mtime=stat.st_mtime))
    items.sort(key=lambda item: (item.type != "directory", item.name.casefold()))
    return FileListResponse(root_id=root_id, path=path, items=items)


def delete_path(root_id: str, path: str, settings: AppConfig | None = None) -> FileOperationResponse:
    absolute = resolve_path(root_id, path, settings=settings, allow_root=False)
    if not os.path.lexists(absolute):
        raise FileNotFoundError("路径不存在")
    if os.path.islink(absolute):
        raise UnsafePathError("不允许操作符号链接")
    os.remove(absolute) if os.path.isfile(absolute) else shutil.rmtree(absolute)
    return FileOperationResponse(message="删除成功")


def move_path(root_id: str, source_path: str, destination_path: str, settings: AppConfig | None = None) -> FileOperationResponse:
    source = resolve_path(root_id, source_path, settings=settings, allow_root=False)
    destination = resolve_path(root_id, destination_path, settings=settings, allow_root=False)
    if not os.path.exists(source):
        raise FileNotFoundError("源路径不存在")
    if os.path.islink(source):
        raise UnsafePathError("不允许操作符号链接")
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    destination = resolve_path(root_id, destination_path, settings=settings, allow_root=False)
    shutil.move(source, destination)
    return FileOperationResponse(message="移动成功")


def rename_path(root_id: str, path: str, new_name: str, settings: AppConfig | None = None) -> FileOperationResponse:
    if not new_name or os.path.basename(new_name) != new_name or new_name in {".", ".."}:
        raise UnsafePathError("新名称不能包含路径")
    parent = str(PurePosixPath(path.replace(chr(92), "/")).parent)
    destination = new_name if parent == "." else f"{parent}/{new_name}"
    return move_path(root_id, path, destination, settings)


def create_path(root_id: str, path: str, kind: str, settings: AppConfig | None = None) -> FileOperationResponse:
    absolute = resolve_path(root_id, path, settings=settings, allow_root=False)
    if os.path.lexists(absolute):
        raise FileExistsError("路径已存在")
    if kind == "directory":
        os.makedirs(absolute)
    elif kind == "file":
        os.makedirs(os.path.dirname(absolute), exist_ok=True)
        absolute = resolve_path(root_id, path, settings=settings, allow_root=False)
        with open(absolute, "x", encoding="utf-8"):
            pass
    else:
        raise ValueError("无效的类型，必须是 'file' 或 'directory'")
    return FileOperationResponse(message="创建成功")


def upload_file(file_obj: BinaryIO, filename: str, root_id: str, path: str, settings: AppConfig | None = None) -> FileUploadResponse:
    safe_name = os.path.basename(filename.replace(chr(92), "/"))
    if not safe_name:
        raise ValueError("文件名不能为空")
    directory = resolve_path(root_id, path, settings=settings)
    os.makedirs(directory, exist_ok=True)
    destination_rel = f"{path.rstrip('/')}/{safe_name}".lstrip("/")
    destination = resolve_path(root_id, destination_rel, settings=settings, allow_root=False)
    temporary = os.path.join(directory, f".uploading-{uuid.uuid4().hex}")
    try:
        with open(temporary, "xb") as output:
            shutil.copyfileobj(file_obj, output, length=1024 * 1024)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
    return FileUploadResponse(message="上传成功", root_id=root_id, path=destination_rel)


def upload_media(file_obj: BinaryIO, filename: str, settings: AppConfig | None = None) -> FileUploadResponse:
    settings = settings or get_settings()
    extension = os.path.splitext(os.path.basename(filename))[1].lower()
    if not extension:
        raise ValueError("无法识别文件扩展名")
    upload_dir = settings.get_upload_dir()
    root_id = settings.default_repo_id()
    os.makedirs(upload_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    destination = os.path.join(upload_dir, f"{timestamp}{extension}")
    counter = 1
    while os.path.exists(destination):
        destination = os.path.join(upload_dir, f"{timestamp}_{counter}{extension}")
        counter += 1
    with open(destination, "xb") as output:
        shutil.copyfileobj(file_obj, output, length=1024 * 1024)
    return FileUploadResponse(message="上传成功", root_id=root_id, path=destination)
