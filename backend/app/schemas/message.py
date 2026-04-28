from pydantic import BaseModel
from typing import List, Optional
from app.schemas.base import OrmBase, TimestampMixin, MediaUrlMixin

MEDIA_PREVIEW_LIMIT = 9  # 消息内媒体预览上限（3×3 宫格）


class MessageCreate(BaseModel):
    text: Optional[str] = None
    actor_id: Optional[int] = None
    files: List[str] = []
    tag_ids: Optional[List[int]] = None


class ClientMediaFile(BaseModel):
    id: int           # 客户端提供的 Media ID
    file_path: str    # upload-media 返回的服务器文件路径


class MessageCreateFromClient(BaseModel):
    id: int                            # 客户端提供的 Message ID
    text: Optional[str] = None
    actor_id: Optional[int] = None
    created_at: Optional[str] = None   # ISO 时间戳
    files: List[ClientMediaFile] = []  # 客户端提供 media_id + 服务器文件路径


class MessageUpdate(BaseModel):
    text: Optional[str] = None
    actor_id: Optional[int] = None
    starred: Optional[bool] = None
    created_at: Optional[str] = None  # ISO 时间戳
    media_order: Optional[List[int]] = None  # media_id 数组，定义新的 position 顺序
    tag_ids: Optional[List[int]] = None  # 显式 tag 绑定；传入则替换、不调用文本解析


class MessageMediaItem(MediaUrlMixin):
    mime_type: str | None
    width: int | None
    height: int | None
    duration_ms: int | None
    starred: bool = False
    tags: List['MessageTagItem'] = []


class MessageTagItem(OrmBase):
    id: int
    name: str
    category: str | None = None


class MessageResponse(TimestampMixin):
    id: int
    text: str | None = None
    actor_id: int | None = None
    actor_name: str | None = None
    media_count: int
    starred: bool = False


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


class MessageSplit(BaseModel):
    media_ids: List[int]


class MessageDatesResponse(BaseModel):
    dates: List[MessageDateCount]


class MessageSyncMediaItem(MessageMediaItem):
    file_hash: str = ""
    file_size: int | None = None
    rating: int = 0
    position: int = 0


class MessageSyncResponse(MessageResponse):
    media_items: List[MessageSyncMediaItem]
    tags: List[MessageTagItem] = []
