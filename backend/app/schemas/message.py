from pydantic import BaseModel
from typing import List, Optional


class MessageCreate(BaseModel):
    text: Optional[str] = None
    actor_id: Optional[int] = None
    files: List[str] = []


class MessageResponse(BaseModel):
    id: int
    text: Optional[str]
    actor_id: Optional[int]
    actor_name: Optional[str]
    media_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessageDetailResponse(MessageResponse):
    media_items: List[dict]
    tags: List[dict] = []


class CursorResponse(BaseModel):
    items: List[MessageResponse]
    next_cursor: Optional[str]
    has_more: bool


class MessageDetailCursorResponse(BaseModel):
    items: List[MessageDetailResponse]
    next_cursor: Optional[str]
    has_more: bool
