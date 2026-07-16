from pydantic import model_validator
from typing import Optional
from app.config import config
from app.schemas.base import OrmBase


class PersonResponse(OrmBase):
    id: int
    name: str
    description: Optional[str] = None
    cover_path: Optional[str] = None
    cover_url: str = ""
    cover_abs_path: str = ""
    media_count: int = 0
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def _fill_cover_url(self):
        if not self.cover_url:
            self.cover_url = config.get_person_cover_url(self.id)
        if not self.cover_abs_path:
            self.cover_abs_path = config.get_person_cover_path(self.id)
        return self


class PersonCreate(OrmBase):
    name: str
    description: Optional[str] = None


class PersonUpdate(OrmBase):
    name: Optional[str] = None
    description: Optional[str] = None
