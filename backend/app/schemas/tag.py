from typing import Optional
from app.schemas.base import OrmBase


class TagResponse(OrmBase):
    id: int
    name: str
    category: Optional[str] = None
    message_count: int = 0
