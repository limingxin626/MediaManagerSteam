from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.repository.schemas import RepositoryFileResponse
from app.shared.schemas import MediaUrlMixin, TimestampMixin


class FolderLocationItem(BaseModel):
    id: int
    repo_id: str
    rel_path: str
    name: str
    role: str
    local_path: Optional[str] = None


class FolderTagItem(BaseModel):
    id: int
    name: str
    category: Optional[str] = None


class FolderTagCount(FolderTagItem):
    folder_count: int = 0


class FolderPreviewItem(MediaUrlMixin):
    name: str
    starred: bool = False
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    video_media_id: Optional[int] = None
    frame_ms: Optional[int] = None
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    source: str


class FolderDetectionInfo(BaseModel):
    source: str = "filename"
    confidence: float = 0.0
    reason: Optional[str] = None
    ambiguous: bool = False


class FolderMediaEntry(BaseModel):
    id: str
    kind: str
    title: str
    sequence: Optional[int] = None
    season_number: Optional[int] = None
    episode_numbers: List[int] = Field(default_factory=list)
    files: List[RepositoryFileResponse] = Field(default_factory=list)
    detection: FolderDetectionInfo = Field(default_factory=FolderDetectionInfo)


class FolderArtwork(BaseModel):
    poster: Optional[RepositoryFileResponse] = None
    fanart: Optional[RepositoryFileResponse] = None


class FolderResponse(TimestampMixin):
    id: int
    name: str
    collection_id: Optional[int] = None
    collection_name: Optional[str] = None
    issue_id: Optional[int] = None
    issue_title: Optional[str] = None
    starred: bool = False
    kind: str = "unknown"
    location_count: int
    media_count: int
    primary_repo_id: Optional[str] = None
    primary_folder_path: Optional[str] = None
    tags: List[FolderTagItem] = []
    preview_files: List[RepositoryFileResponse] = []
    fanart_file: Optional[RepositoryFileResponse] = None
    poster_file: Optional[RepositoryFileResponse] = None
    # 作品发行日期(ISO);无则 None,区别于 created_at(入库时间)
    released_at: Optional[str] = None

    @field_validator("released_at", mode="before")
    @classmethod
    def convert_released_at_to_str(cls, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class FolderDetailResponse(FolderResponse):
    artwork: FolderArtwork = Field(default_factory=FolderArtwork)
    entries: List[FolderMediaEntry] = Field(default_factory=list)
    gallery: List[RepositoryFileResponse] = Field(default_factory=list)
    extras: List[FolderMediaEntry] = Field(default_factory=list)
    unclassified: List[RepositoryFileResponse] = Field(default_factory=list)
    primary_entry_id: Optional[str] = None
    detection: FolderDetectionInfo = Field(default_factory=FolderDetectionInfo)
    locations: List[FolderLocationItem] = Field(default_factory=list)
    files: List[RepositoryFileResponse] = Field(default_factory=list)
    previews: List[FolderPreviewItem] = Field(default_factory=list)


class FolderUpdateRequest(BaseModel):
    """可更新字段;仅传入的字段生效(空串/显式 null 表示清空 released_at)。"""
    released_at: Optional[str] = None


class FolderCursorResponse(BaseModel):
    items: List[FolderResponse]
    next_cursor: Optional[str] = None
    has_more: bool
