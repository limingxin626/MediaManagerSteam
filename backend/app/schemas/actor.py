from pydantic import BaseModel, model_validator
from typing import List, Optional
from app.config import config
from app.schemas.base import OrmBase


class ActorResponse(OrmBase):
    id: int
    name: str
    description: Optional[str] = None
    avatar_path: Optional[str] = None
    avatar_url: str = ""
    avatar_abs_path: str = ""
    message_count: int
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def _fill_avatar_url(self):
        if not self.avatar_url:
            self.avatar_url = config.get_actor_avatar_url(self.id)
        if not self.avatar_abs_path:
            self.avatar_abs_path = config.get_actor_avatar_path(self.id)
        return self


class ActorDetailResponse(ActorResponse):
    messages: List[dict]


class ActorListResponse(BaseModel):
    items: List[ActorResponse]
    no_actor_count: int


class ActorSyncResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
