from pydantic import BaseModel, model_validator
from typing import List, Optional
from app.config import config


class MediaResponse(BaseModel):
    id: int
    file_path: str
    file_url: str = ""
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    rating: int
    starred: bool = False
    view_count: int
    thumb_url: str = ""
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _fill_urls(self):
        # 自动填充缩略图URL
        if not self.thumb_url:
            self.thumb_url = f"/asktao/data/thumbs/{self.id}.webp"
        # 将绝对路径转换为URL路径
        if not self.file_url and self.file_path:
            self.file_url = config.to_url_path(self.file_path)
        return self


class MediaDetailResponse(MediaResponse):
    messages: List[dict]


class MediaCursorResponse(BaseModel):
    items: List[MediaResponse]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_more: bool
    has_more_before: bool = False
