import time
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Any, Optional
import os
import shutil
from pydantic import BaseModel
from app.config import config
from app.schemas.file import FileUploadResponse

router = APIRouter(prefix="/files", tags=["files"])

class FileInfo(BaseModel):
    name: str
    path: str
    type: str
    size: Optional[int]
    mtime: float

class FileListResponse(BaseModel):
    path: str
    items: List[FileInfo]

class FileOperationResponse(BaseModel):
    message: str

class FileUploadResponse(BaseModel):
    message: str
    path: str

class FileManager:
    @staticmethod
    def list_path(path: str = ".") -> FileListResponse:
        """列出指定路径下的文件和文件夹"""
        try:
            # 确保路径存在
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail="路径不存在")
            
            items = []
            # 遍历路径下的所有项目
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                item_info = FileInfo(
                    name=item,
                    path=item_path,
                    type="directory" if os.path.isdir(item_path) else "file",
                    size=os.path.getsize(item_path) if os.path.isfile(item_path) else None,
                    mtime=os.path.getmtime(item_path)
                )
                items.append(item_info)
            
            return FileListResponse(
                path=path,
                items=items
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def delete_path(path: str) -> FileOperationResponse:
        """删除文件或文件夹"""
        try:
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail="路径不存在")
            
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
            
            return FileOperationResponse(message="删除成功")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def move_path(source_path: str, destination_path: str) -> FileOperationResponse:
        """移动文件或文件夹"""
        try:
            if not os.path.exists(source_path):
                raise HTTPException(status_code=404, detail="源路径不存在")
            
            # 确保目标路径的父目录存在
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            shutil.move(source_path, destination_path)
            return FileOperationResponse(message="移动成功")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def rename_path(path: str, new_name: str) -> FileOperationResponse:
        """重命名文件或文件夹"""
        try:
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail="路径不存在")
            
            # 构建新路径
            parent_dir = os.path.dirname(path)
            new_path = os.path.join(parent_dir, new_name)
            
            os.rename(path, new_path)
            return FileOperationResponse(message="重命名成功")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def create_path(path: str, type: str) -> FileOperationResponse:
        """创建文件或文件夹"""
        try:
            if os.path.exists(path):
                raise HTTPException(status_code=400, detail="路径已存在")
            
            if type == "directory":
                os.makedirs(path, exist_ok=True)
            elif type == "file":
                # 确保父目录存在
                parent_dir = os.path.dirname(path)
                if parent_dir and not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)
                open(path, 'a').close()
            else:
                raise HTTPException(status_code=400, detail="无效的类型，必须是 'file' 或 'directory'")
            
            return FileOperationResponse(message="创建成功")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def upload_file(file: UploadFile, path: str = ".") -> FileUploadResponse:
        """上传文件"""
        try:
            # 确保目标路径存在
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            
            # 构建文件保存路径
            file_path = os.path.join(path, file.filename)
            
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(file.file.read())
            
            return FileUploadResponse(message="上传成功", path=file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=FileListResponse, summary="列出路径下的文件和文件夹")
async def list_path(path: Optional[str] = "."):
    """
    列出指定路径下的所有文件和文件夹信息
    
    参数:
    - path: 要列出的路径，默认为当前目录
    
    返回:
    - path: 当前路径
    - items: 文件和文件夹列表，每个项目包含名称、路径、类型、大小和修改时间
    """
    return FileManager.list_path(path)

@router.delete("/delete", response_model=FileOperationResponse, summary="删除文件或文件夹")
async def delete_path(path: str):
    """
    删除指定的文件或文件夹
    
    参数:
    - path: 要删除的文件或文件夹路径
    
    返回:
    - message: 操作结果消息
    """
    return FileManager.delete_path(path)

@router.post("/move", response_model=FileOperationResponse, summary="移动文件或文件夹")
async def move_path(source_path: str, destination_path: str):
    """
    移动文件或文件夹到新位置
    
    参数:
    - source_path: 源文件或文件夹路径
    - destination_path: 目标文件或文件夹路径
    
    返回:
    - message: 操作结果消息
    """
    return FileManager.move_path(source_path, destination_path)

@router.put("/rename", response_model=FileOperationResponse, summary="重命名文件或文件夹")
async def rename_path(path: str, new_name: str):
    """
    重命名文件或文件夹
    
    参数:
    - path: 要重命名的文件或文件夹路径
    - new_name: 新的名称
    
    返回:
    - message: 操作结果消息
    """
    return FileManager.rename_path(path, new_name)

@router.post("/create", response_model=FileOperationResponse, summary="创建文件或文件夹")
async def create_path(path: str, type: str):
    """
    创建新的文件或文件夹
    
    参数:
    - path: 要创建的文件或文件夹路径
    - type: 类型，必须是 'file' 或 'directory'
    
    返回:
    - message: 操作结果消息
    """
    return FileManager.create_path(path, type)

@router.post("/upload", response_model=FileUploadResponse, summary="上传文件")
async def upload_file(
    file: UploadFile = File(...),
    path: str = Form(".")
):
    """
    上传文件到指定路径
    
    参数:
    - file: 要上传的文件
    - path: 上传目标路径，默认为当前目录
    
    返回:
    - message: 操作结果消息
    - path: 上传后的文件路径
    """
    return FileManager.upload_file(file, path)


@router.post("/upload-media", response_model=FileUploadResponse, status_code=201, summary="上传媒体文件")
async def upload_media(file: UploadFile = File(...)):
    """
    上传媒体文件（图片/视频），自动存入按日期组织的目录。
    返回的 file_path 可直接用于 POST /messages 的 files 字段。
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if not ext:
        raise HTTPException(status_code=400, detail="无法识别文件扩展名")

    upload_dir = config.get_upload_dir()
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    dest_path = os.path.join(upload_dir, f"{timestamp}{ext}")
    counter = 1
    while os.path.exists(dest_path):
        dest_path = os.path.join(upload_dir, f"{timestamp}_{counter}{ext}")
        counter += 1
    try:
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        await file.close()

    return FileUploadResponse(message="上传成功", path=dest_path)
