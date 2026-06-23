"""磁盘扫描视图(`fs_entry`)的响应 schema。

`FsEntryResponse` 不用 MediaUrlMixin —— 因为 thumb_url 条件依赖 media_id:
匹配到 Media 的行复用 `/data/thumbs/{media_id}.webp`,否则用自己生成的
`/data/scan_thumbs/{fs_entry_id}.webp`。
"""
from datetime import datetime
from typing import List, Optional

from pydantic import field_validator, model_validator

from app.config import config
from app.schemas.base import OrmBase


class FsEntryResponse(OrmBase):
    id: int
    repo_id: str = ""
    rel_path: str
    file_path: str = ""            # 镜像 rel_path,给前端与 Media 字段名对齐
    mime_type: Optional[str] = None
    media_type: str
    file_size: Optional[int] = None
    mtime: float                   # 裸 epoch float:前端格式化 + 游标用同一值
    scanned_at: str
    media_id: Optional[int] = None
    meta_status: str
    thumb_status: str

    # metadata(worker / reused 填充)
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    fps: Optional[float] = None
    bitrate: Optional[int] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    has_audio: Optional[int] = None
    taken_at: Optional[datetime] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    orientation: Optional[int] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens: Optional[str] = None
    is_hdr: Optional[int] = None
    color_transfer: Optional[str] = None

    # 拼接产出
    file_url: str = ""
    thumb_url: str = ""
    local_file_path: str = ""
    local_thumb_path: str = ""    # 本机绝对路径(Electron file:// 直读),按 media_id 条件指向

    @field_validator("scanned_at", mode="before")
    @classmethod
    def _scanned_at_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @model_validator(mode="after")
    def _fill(self):
        if not self.file_path:
            self.file_path = self.rel_path
        if not self.file_url and self.repo_id and self.rel_path:
            self.file_url = config.url_for(self.repo_id, self.rel_path)
        if not self.local_file_path and self.repo_id and self.rel_path:
            ab = config.resolve_to_absolute(self.repo_id, self.rel_path)
            if ab:
                self.local_file_path = ab
        # 缩略图:匹配到 Media 且复用 → 指向 Media 缩略图;否则指向自有 scan_thumb。
        # thumb_url(HTTP,相对)与 local_thumb_path(本机绝对,Electron file://)同一分支,
        # 与 /media 的 MediaUrlMixin 行为对齐。
        reuse = self.media_id is not None and self.thumb_status == "reused"
        if not self.thumb_url:
            self.thumb_url = (
                config.get_thumbnail_url(self.media_id) if reuse
                else config.get_scan_thumbnail_url(self.id)
            )
        if not self.local_thumb_path:
            self.local_thumb_path = (
                config.get_thumbnail_path(self.media_id) if reuse
                else config.get_scan_thumbnail_path(self.id)
            )
        return self


class FsEntryCursorResponse(OrmBase):
    items: List[FsEntryResponse]
    next_cursor: Optional[str] = None
    has_more: bool


class ScanStatusResponse(OrmBase):
    total: int
    pending: int
    done: int
    failed: int
    running: bool
