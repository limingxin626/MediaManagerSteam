from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from datetime import datetime
from app.config import config


class OrmBase(BaseModel):
    """所有 ORM 映射 schema 的基类，统一 from_attributes 配置"""
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(OrmBase):
    """带 created_at / updated_at 的 ORM schema 基类"""
    created_at: str
    updated_at: str

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def convert_datetime_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class MediaUrlMixin(OrmBase):
    """自动填充 file_url / thumb_url 的 mixin。

    file_url 优先用 (repo_id, file_path) 通过 url_for() 拼出;
    若 repo 未注册(如迁移期 `__legacy__` 行,或老客户端不传 repo_id),
    再兜底走 to_url_path(把 file_path 当作绝对路径解)。
    """
    id: int
    file_path: str
    repo_id: str = ""
    file_url: str = ""
    thumb_path: str = ""
    thumb_url: str = ""

    @model_validator(mode="after")
    def _fill_urls(self):
        if not self.thumb_url:
            self.thumb_url = config.get_thumbnail_url(self.id)
        if not self.thumb_path:
            self.thumb_path = config.get_thumbnail_path(self.id)
        if not self.file_url and self.file_path:
            url = config.url_for(self.repo_id, self.file_path) if self.repo_id else ""
            if not url:
                url = config.to_url_path(self.file_path)
            self.file_url = url
        return self
