from pydantic import BaseModel, model_validator
from typing import List, Optional
from app.config import config
from app.schemas.base import OrmBase


class CollectionResponse(OrmBase):
    id: int
    name: str
    description: Optional[str] = None
    cover_path: Optional[str] = None
    cover_url: str = ""
    cover_abs_path: str = ""
    message_count: int
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def _fill_cover_url(self):
        if not self.cover_url:
            self.cover_url = config.get_collection_cover_url(self.id)
        if not self.cover_abs_path:
            self.cover_abs_path = config.get_collection_cover_path(self.id)
        return self


class CollectionDetailResponse(CollectionResponse):
    messages: List[dict]


class CollectionListResponse(BaseModel):
    items: List[CollectionResponse]
    no_collection_count: int


class CollectionSyncResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    cover: Optional[str] = None


class CollectionCreate(OrmBase):
    name: str
    description: Optional[str] = None


class CollectionUpdate(OrmBase):
    name: Optional[str] = None
    description: Optional[str] = None
