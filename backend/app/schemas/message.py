from pydantic import BaseModel, model_validator
from typing import List, Optional

MEDIA_PREVIEW_LIMIT = 9  # 消息内媒体预览上限（3×3 宫格）


class MessageCreate(BaseModel):
    text: Optional[str] = None
    actor_id: Optional[int] = None
    files: List[str] = []


class MessageUpdate(BaseModel):
    text: Optional[str] = None
    actor_id: Optional[int] = None
    starred: Optional[bool] = None
    media_order: Optional[List[int]] = None  # media_id 数组，定义新的 position 顺序


class MessageMediaItem(BaseModel):
    id: int
    file_path: str
    mime_type: Optional[str] = None
    duration: Optional[int] = None
    thumb_url: str = ""

    @model_validator(mode="after")
    def _fill_thumb_url(self):
        if not self.thumb_url:
            self.thumb_url = f"/data/thumbs/{self.id}.webp"
        return self


class MessageTagItem(BaseModel):
    id: int
    name: str
    category: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    text: Optional[str] = None
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    media_count: int
    starred: bool = False
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessageDetailResponse(MessageResponse):
    media_items: List[MessageMediaItem]
    tags: List[MessageTagItem] = []


class CursorResponse(BaseModel):
    items: List[MessageResponse]
    next_cursor: Optional[str] = None
    has_more: bool


class MessageDetailCursorResponse(BaseModel):
    items: List[MessageDetailResponse]
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    has_more: bool
    has_more_before: bool = False


class MessageDateCount(BaseModel):
    date: str
    count: int


class MessageMerge(BaseModel):
    message_ids: List[int]  # 要合并的消息 ID 列表，第一个为目标消息


class MessageDatesResponse(BaseModel):
    dates: List[MessageDateCount]
