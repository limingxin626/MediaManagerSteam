from pydantic import BaseModel, model_validator, field_validator
from typing import List, Optional
from datetime import datetime
from app.config import config

MEDIA_PREVIEW_LIMIT = 9  # 消息内媒体预览上限（3×3 宫格）


class MessageCreate(BaseModel):
    text: Optional[str] = None
    actor_id: Optional[int] = None
    files: List[str] = []


class MessageCreateFromClient(BaseModel):
    id: int                            # 客户端提供的 Message ID
    text: Optional[str] = None
    actor_id: Optional[int] = None
    created_at: Optional[str] = None   # ISO 时间戳
    files: List[str] = []              # upload-media 返回的服务器文件路径


class MessageUpdate(BaseModel):
    text: Optional[str] = None
    actor_id: Optional[int] = None
    starred: Optional[bool] = None
    media_order: Optional[List[int]] = None  # media_id 数组，定义新的 position 顺序


class MessageMediaItem(BaseModel):
    id: int
    file_path: str
    file_url: str = ""
    mime_type: Optional[str] = None
    duration_ms: Optional[int] = None
    thumb_url: str = ""
    starred: bool = False

    @model_validator(mode="after")
    def _fill_urls(self):
        # 自动填充缩略图URL
        if not self.thumb_url:
            self.thumb_url = f"/asktao/data/thumbs/{self.id}.webp"
        # 将绝对路径转换为URL路径
        if not self.file_url and self.file_path:
            self.file_url = config.to_url_path(self.file_path)
        return self

    class Config:
        from_attributes = True


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

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def convert_datetime_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

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


class MessageSyncMediaItem(BaseModel):
    id: int
    file_url: str = ""
    file_path: str
    file_hash: str = ""
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    rating: int = 0
    starred: bool = False
    thumb_url: str = ""
    position: int = 0

    @model_validator(mode="after")
    def _fill_urls(self):
        if not self.thumb_url:
            self.thumb_url = f"/asktao/data/thumbs/{self.id}.webp"
        if not self.file_url and self.file_path:
            self.file_url = config.to_url_path(self.file_path)
        return self

    class Config:
        from_attributes = True


class MessageSyncResponse(BaseModel):
    id: int
    text: Optional[str] = None
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    starred: bool = False
    created_at: str
    updated_at: str
    media_items: List[MessageSyncMediaItem]
    tags: List[MessageTagItem] = []

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def convert_datetime_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    class Config:
        from_attributes = True
