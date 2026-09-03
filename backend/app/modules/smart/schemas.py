"""Smart-search HTTP schemas."""
from typing import List, Optional
from pydantic import BaseModel


class SuggestRequest(BaseModel):
    media_id: int
    top_k: int = 10


class TagSuggestion(BaseModel):
    tag_id: int
    name: str
    category: Optional[str] = None
    score: float


class ApplyRequest(BaseModel):
    media_id: int
    tag_ids: List[int]


class RebuildRequest(BaseModel):
    media_ids: Optional[List[int]] = None
