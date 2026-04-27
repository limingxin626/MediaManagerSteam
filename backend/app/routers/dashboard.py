"""
主页 dashboard.md 文件读写。

GET  /api/dashboard         返回 {content, mtime}
PUT  /api/dashboard         body: {content, if_match}
                            mtime 不一致 → 409 + 当前内容
                            一致      → 原子写入，返回新 mtime
"""
import logging
import os
import tempfile

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import config, DASHBOARD_DEFAULT_CONTENT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardResponse(BaseModel):
    content: str
    mtime: float


class DashboardUpdate(BaseModel):
    content: str
    if_match: float


class DashboardConflict(BaseModel):
    detail: str
    current_mtime: float
    current_content: str


def _ensure_file() -> str:
    path = config.get_dashboard_md_path()
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(DASHBOARD_DEFAULT_CONTENT)
        logger.info("dashboard.md 不存在，已创建默认模板：%s", path)
    return path


def _read(path: str) -> DashboardResponse:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return DashboardResponse(content=content, mtime=os.path.getmtime(path))


@router.get("", response_model=DashboardResponse)
def get_dashboard():
    path = _ensure_file()
    return _read(path)


@router.put("", response_model=DashboardResponse)
def put_dashboard(payload: DashboardUpdate):
    path = _ensure_file()
    current_mtime = os.path.getmtime(path)

    # 浮点 mtime 比较：放宽到毫秒级，避免不同文件系统精度差异误判
    if abs(current_mtime - payload.if_match) > 1e-3:
        with open(path, "r", encoding="utf-8") as f:
            current_content = f.read()
        raise HTTPException(
            status_code=409,
            detail={
                "message": "conflict",
                "current_mtime": current_mtime,
                "current_content": current_content,
            },
        )

    # 原子写入：同目录临时文件 + os.replace
    dir_name = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(prefix=".dashboard.", suffix=".tmp", dir=dir_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload.content)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    return _read(path)
