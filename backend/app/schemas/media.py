from pydantic import BaseModel, model_validator
from typing import List, Optional


class MediaResponse(BaseModel):
    id: int
    file_path: str
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
    def _fill_thumb_url(self):
        if not self.thumb_url:
            self.thumb_url = f"/data/thumbs/{self.id}.webp"
        return self


class MediaDetailResponse(MediaResponse):
    messages: List[dict]


class MediaCursorResponse(BaseModel):
    items: List[MediaResponse]
    next_cursor: Optional[str] = None
    has_more: bool
