from pydantic import BaseModel
from typing import Optional


class TagResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    message_count: int = 0

    class Config:
        from_attributes = True
