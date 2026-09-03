from pydantic import BaseModel
from typing import Optional, List


class FileInfo(BaseModel):
    """文件/文件夹信息模型"""
    name: str
    path: str
    type: str  # 'file' 或 'directory'
    size: Optional[int]  # 文件大小（字节），文件夹为None
    mtime: float  # 修改时间戳


class FileListResponse(BaseModel):
    """文件列表响应模型"""
    root_id: str
    path: str
    items: List[FileInfo]


class FileOperationResponse(BaseModel):
    """文件操作响应模型"""
    message: str


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    message: str
    root_id: str | None = None
    path: str
