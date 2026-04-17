from pydantic import BaseModel, model_validator, field_validator
from typing import List, Optional
from datetime import datetime
from app.config import config


class MediaResponse(BaseModel):
    id: int
    file_path: str
    file_url: str = ""
    file_size: int | None
    mime_type: str | None
    width: int | None
    height: int | None
    duration_ms: int | None
    rating: int
    starred: bool = False
    view_count: int
    thumb_url: str = ""
    created_at: str
    updated_at: str

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def convert_datetime_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _fill_urls(self):
        # 自动填充缩略图URL
        if not self.thumb_url:
            self.thumb_url = config.get_thumbnail_url(self.id)
        # 将绝对路径转换为URL路径
        if not self.file_url and self.file_path:
            self.file_url = config.to_url_path(self.file_path)
        return self


class MediaDetailResponse(MediaResponse):
    messages: List[dict]

    class Config:
        from_attributes = True


class MediaCursorResponse(BaseModel):
    items: List[MediaResponse]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_more: bool
    has_more_before: bool = False
