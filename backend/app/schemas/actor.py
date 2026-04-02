from pydantic import BaseModel, model_validator
from typing import List, Optional


class ActorResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    avatar_path: Optional[str] = None
    avatar_url: str = ""
    message_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _fill_avatar_url(self):
        if not self.avatar_url:
            self.avatar_url = f"/data/actor_cover/{self.id}.webp"
        return self


class ActorDetailResponse(ActorResponse):
    messages: List[dict]


class ActorSyncResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
