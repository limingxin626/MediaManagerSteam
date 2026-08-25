from typing import List, Optional

from pydantic import BaseModel

from app.schemas.base import MediaUrlMixin, TimestampMixin
from app.schemas.repositories import RepositoryFileResponse


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
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    video_media_id: Optional[int] = None
    frame_ms: Optional[int] = None
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    source: str


class FolderResponse(TimestampMixin):
    id: int
    name: str
    collection_id: Optional[int] = None
    collection_name: Optional[str] = None
    issue_id: Optional[int] = None
    issue_title: Optional[str] = None
    starred: bool = False
    location_count: int
    media_count: int
    primary_repo_id: Optional[str] = None
    primary_folder_path: Optional[str] = None
    tags: List[FolderTagItem] = []
    preview_files: List[RepositoryFileResponse] = []
    fanart_file: Optional[RepositoryFileResponse] = None
    poster_file: Optional[RepositoryFileResponse] = None


class FolderDetailResponse(FolderResponse):
    locations: List[FolderLocationItem] = []
    files: List[RepositoryFileResponse] = []
    previews: List[FolderPreviewItem] = []


class FolderCursorResponse(BaseModel):
    items: List[FolderResponse]
    next_cursor: Optional[int] = None
    has_more: bool
