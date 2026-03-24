from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime, date

from sqlalchemy.sql.operators import op
from app.schemas.file import FileInfo, FileListResponse, FileOperationResponse, FileUploadResponse


# 标签相关模型
class TagBase(BaseModel):
    category: str
    name: str

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    category: Optional[str] = None
    name: Optional[str] = None

class Tag(TagBase):
    id: int

    class Config:
        from_attributes = True

# 标签同步响应模型
class TagSync(BaseModel):
    id: int
    name: str
    category: str
    thumbnail: str

    class Config:
        from_attributes = False




# 演员相关模型
class ActorBase(BaseModel):
    name: str
    description: Optional[str] = ""
    aliases: Optional[str] = None
    birth_date: Optional[date] = None
    category: Optional[str] = "默认"
    country: Optional[str] = ""
    body_type: Optional[str] = ""
    breast_size: Optional[str] = ""
    rating: Optional[int] = 0
    download_status: Optional[str] = "未下载"

class Actor(ActorBase):
    id: int
    usage: Optional[int] = 0
    avatar: Optional[str] = ""
    avatar_path: Optional[str] = None

    class Config:
        from_attributes = True

    @validator('category', 'country', 'body_type', 'breast_size', 'download_status', pre=True)
    def enum_to_string(cls, v):
        if v is None:
            return None
        return v.value if hasattr(v, 'value') else v

# 演员分页响应模型
class ActorPagination(BaseModel):
    items: list[Actor]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True


# 分组相关模型
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    serial_number: Optional[str] = None
    release_date: Optional[date] = None
    rating: Optional[int] = None
    actor_id: int

    size: Optional[int] = 0
    media_cnt: Optional[int] = 0

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    serial_number: Optional[str] = None
    release_date: Optional[date] = None
    rating: Optional[int] = None
    actor_id: Optional[int] = None
    size: Optional[int] = None
    media_cnt: Optional[int] = None
    thumbnail: Optional[str] = None

class Group(GroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    thumbnail: Optional[str] = None

    class Config:
        from_attributes = True

# 分组分页响应模型
class GroupPagination(BaseModel):
    items: list[Group]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True



# 媒体相关模型
class MediaSimple(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    duration: Optional[int] = None
    rating: Optional[int] = None
    remote_thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True

# 媒体分页响应模型
class MediaPagination(BaseModel):
    items: list[MediaSimple]
    total: int
    skip: int
    limit: int

    class Config:
        from_attributes = True

class MediaBase(BaseModel):
    name: str
    description: Optional[str] = None

    type: Optional[str] = None
    local_media_path: str
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    date: Optional[date]
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

    rating: Optional[int] = None
    view_count: Optional[int] = 0
    last_viewed_at: Optional[datetime] = None

    remote_media_url: Optional[str] = ""

    start_time: Optional[float] = None
    timestamp: Optional[float] = None
    end_time: Optional[float] = None

    actor_id: Optional[int] = None
    group_id: Optional[int] = None
    parent_id: Optional[int] = None

class Media(MediaBase):
    id: int
    created_at: datetime
    updated_at: datetime
    remote_thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True


class MediaCreate(MediaBase):
    pass

class MediaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    local_media_path: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    type: Optional[str] = None
    file_hash: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    rating: Optional[int] = None
    view_count: Optional[int] = None
    last_viewed_at: Optional[datetime] = None
    group_id: Optional[int] = None
    timestamp: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    date: Optional[date] = None
    parent_id: Optional[int] = None
    actor_id: Optional[int] = None
    # 保留原有字段用于兼容
    remote_thumbnail_url: Optional[str] = None
    remote_media_url: Optional[str] = None
    size: Optional[int] = None
    hash: Optional[str] = None
    usage: Optional[int] = None
    startTime: Optional[float] = None
    endTime: Optional[float] = None


class MediaPreview(BaseModel):
    id: int
    name: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    timestamp: Optional[float] = None

# 媒体标签关联模型
class MediaTag(BaseModel):
    media_id: int
    tag_id: int




# 文章相关模型
class Article(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    author: str



# 演员详情响应模型（包含分组信息）
class ActorDetail(Actor):
    groups: list["Group"] = []
    media: list["MediaSimple"] = []

    class Config:
        from_attributes = True

# 分组详情响应模型（包含媒体信息）
class GroupDetail(Group):
    media: list["MediaSimple"] = []
    actor: Actor

    class Config:
        from_attributes = True

# 媒体详情响应模型（包含演员和分组信息）
class MediaDetail(Media):
    group: Optional[Group] = None
    actor: Optional[Actor] = None
    tags: list["Tag"] = []
    previews: list[MediaPreview] = []

    class Config:
        from_attributes = True
