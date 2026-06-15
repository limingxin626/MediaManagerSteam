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
    """自动填充 6 个 path/URL 字段,语义见 CLAUDE.md「Pydantic schema validators」段。

    - `repo_id` / `file_path` 来自 DB,后者是相对 repo 根的 forward-slash 路径
    - `local_*_path` 是本机绝对路径,Vue/Electron 用 `file://` 直读
    - `*_url` 是相对 URL,Android 用 sync baseUrl 拼接,Vue 走 HTTP fallback

    repo 未注册(老 `__legacy__` 数据或外接盘没插) → local_file_path / file_url 留空串,
    客户端按需 fallback 到占位 UI。
    """
    id: int
    repo_id: str = ""
    file_path: str
    local_file_path: str = ""
    local_thumb_path: str = ""
    file_url: str = ""
    thumb_url: str = ""

    @model_validator(mode="after")
    def _fill_urls(self):
        if not self.thumb_url:
            self.thumb_url = config.get_thumbnail_url(self.id)
        if not self.local_thumb_path:
            self.local_thumb_path = config.get_thumbnail_path(self.id)
        if self.file_path and self.repo_id:
            if not self.file_url:
                self.file_url = config.url_for(self.repo_id, self.file_path)
            if not self.local_file_path:
                abs_path = config.resolve_to_absolute(self.repo_id, self.file_path)
                if abs_path:
                    self.local_file_path = abs_path
        return self
