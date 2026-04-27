from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from app.schemas.base import TimestampMixin, MediaUrlMixin
from app.schemas.message import MessageTagItem


class MediaResponse(MediaUrlMixin, TimestampMixin):
    file_size: int | None
    mime_type: str | None
    width: int | None
    height: int | None
    duration_ms: int | None
    rating: int
    starred: bool = False
    view_count: int
    tags: List[MessageTagItem] = []
    video_media_id: int | None = None
    frame_ms: int | None = None
    start_ms: int | None = None
    end_ms: int | None = None


class MediaDetailResponse(MediaResponse):
    messages: List[dict]


class TimelineItem(BaseModel):
    year: int
    month: int
    count: int


class MediaCursorResponse(BaseModel):
    items: List[MediaResponse]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_more: bool
    has_more_before: bool = False


class VideoPreviewItem(MediaUrlMixin):
    """视频预览（章节）条目。继承 MediaUrlMixin 自动获得 id/file_url/thumb_url。"""
    mime_type: str | None = None
    frame_ms: int
    start_ms: int | None = None
    end_ms: int | None = None
    model_config = ConfigDict(from_attributes=True)


class VideoPreviewCreate(BaseModel):
    preview_media_id: int
    frame_ms: int
    start_ms: int | None = None
    end_ms: int | None = None


class VideoPreviewUpdate(BaseModel):
    frame_ms: int | None = None
    start_ms: int | None = None
    end_ms: int | None = None
