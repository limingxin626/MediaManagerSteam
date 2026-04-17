from pydantic import BaseModel
from typing import List, Optional
from app.schemas.base import TimestampMixin, MediaUrlMixin


class MediaResponse(MediaUrlMixin, TimestampMixin):
    file_size: int | None
    mime_type: str | None
    width: int | None
    height: int | None
    duration_ms: int | None
    rating: int
    starred: bool = False
    view_count: int


class MediaDetailResponse(MediaResponse):
    messages: List[dict]


class MediaCursorResponse(BaseModel):
    items: List[MediaResponse]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_more: bool
    has_more_before: bool = False
