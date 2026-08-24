from typing import List, Optional

from pydantic import BaseModel

from app.schemas.base import TimestampMixin
from app.schemas.repositories import RepositoryFileResponse


class FolderLocationItem(BaseModel):
    id: int
    repo_id: str
    rel_path: str
    name: str
    role: str


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


class FolderDetailResponse(FolderResponse):
    locations: List[FolderLocationItem] = []
    files: List[RepositoryFileResponse] = []


class FolderCursorResponse(BaseModel):
    items: List[FolderResponse]
    next_cursor: Optional[int] = None
    has_more: bool