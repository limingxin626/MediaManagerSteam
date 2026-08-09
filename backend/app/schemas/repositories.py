"""Repository catalog response schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import config
from app.schemas.base import OrmBase


class RepositoryFileResponse(OrmBase):
    id: int
    repo_id: str
    folder_id: int
    rel_path: str
    name: str
    file_path: str = ""
    mime_type: Optional[str] = None
    media_type: str
    file_size: Optional[int] = None
    mtime: float
    scanned_at: str
    media_id: Optional[int] = None
    materialize_status: str
    materialize_error: Optional[str] = None
    file_url: str = ""
    thumb_url: str = ""
    local_file_path: str = ""
    local_thumb_path: str = ""
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

    @field_validator("scanned_at", mode="before")
    @classmethod
    def _date_to_str(cls, value):
        return value.isoformat() if isinstance(value, datetime) else value

    @model_validator(mode="after")
    def _fill_urls(self):
        self.file_path = self.file_path or self.rel_path
        self.file_url = self.file_url or config.url_for(self.repo_id, self.rel_path)
        self.local_file_path = self.local_file_path or (
            config.resolve_to_absolute(self.repo_id, self.rel_path) or ""
        )
        if self.media_id is not None:
            self.thumb_url = self.thumb_url or config.get_thumbnail_url(self.media_id)
            self.local_thumb_path = self.local_thumb_path or config.get_thumbnail_path(self.media_id)
        return self


class RepositoryFolderResponse(OrmBase):
    id: int
    repo_id: str
    rel_path: str
    name: str
    parent_id: Optional[int] = None


class RepositorySummaryResponse(OrmBase):
    repo_id: str
    root_path: str
    online: bool
    folder_count: int
    file_count: int
    pending_count: int


class RepositoryBrowseResponse(OrmBase):
    repository: RepositorySummaryResponse
    folder: RepositoryFolderResponse
    folders: List[RepositoryFolderResponse]
    files: List[RepositoryFileResponse]


class DuplicatePhysicalFileItem(BaseModel):
    id: int
    repo_id: str
    rel_path: str
    local_file_path: str
    file_size: Optional[int] = None
    mtime: float
    is_canonical: bool


class DuplicateFileGroup(BaseModel):
    media_id: int
    repo_id: str
    file_path: str
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    thumb_url: str
    local_thumb_path: str
    files: List[DuplicatePhysicalFileItem]


class DuplicateFileCursorResponse(BaseModel):
    items: List[DuplicateFileGroup]
    next_cursor: Optional[int] = None
    has_more: bool


class DuplicateFileDeleteRequest(BaseModel):
    repository_file_ids: List[int] = Field(min_length=1, max_length=100)


class DuplicateFileDeleteFailure(BaseModel):
    id: int
    message: str


class DuplicateFileDeleteResponse(BaseModel):
    deleted_ids: List[int]
    missing_ids: List[int]
    failures: List[DuplicateFileDeleteFailure]
    remaining_count: int
    canonical_available: bool
    canonical_repo_id: str
    canonical_file_path: str
