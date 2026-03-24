from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Date, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from datetime import datetime, date
import enum
import os

# 创建数据库引擎
DATABASE_URL = "sqlite:///./db.sqlite3"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 枚举类型定义
class MediaType(str, enum.Enum):
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    PREVIEW = "PREVIEW"

class ActorCategory(str, enum.Enum):
    SINGLE = "单独"
    LEAKAGE = "泄密"
    PROFESSIONAL = "专业"
    FLJ = "FLJ"
    AV = "AV"
    PENDING = "悬案"
    UNCLASSIFIED = "未分类"

class Country(str, enum.Enum):
    CHINA = "中国"
    KOREA = "韩国"
    TAIWAN = "台湾"
    JAPAN = "日本"
    SEA = "东南亚"
    RUSSIA = "东欧"
    WESTERN = "欧美"

class BreastSize(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"

class BodyType(str, enum.Enum):
    SLIM = "苗条"
    JIMMY = "健美"
    CURVY = "微坦"
    TANK = "坦克"
    GENERAL = "一般"

class DownloadStatus(str, enum.Enum):
    NOT_DOWNLOADED = "未下载"
    NON_ORIGINAL = "非原档"
    ORIGINAL = "原档"


class Actor(Base):
    __tablename__ = "actor"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False, index=True)
    description = Column(Text, default="", nullable=True)
    aliases = Column(Text, nullable=True)
    birth_date = Column(Date, nullable=True)

    # 分类
    category = Column(Enum(ActorCategory), nullable=True, index=True)
    country = Column(Enum(Country), nullable=True, index=True)
    body_type = Column(Enum(BodyType), nullable=True)
    breast_size = Column(Enum(BreastSize), nullable=True)
    rating = Column(Integer, default=0, index=True)
    download_status = Column(Enum(DownloadStatus), default=DownloadStatus.NOT_DOWNLOADED, nullable=False, index=True)

    # 自动
    usage = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    avatar_path = Column(String(1024), nullable=True)

    # 关系
    groups = relationship("Group", back_populates="actor")
    media = relationship("Media", back_populates="actor")
    tags = relationship("Tagging", secondary="actor_tags", back_populates="actors")
    
    @property
    def avatar(self):
        return f"data/actor_cover/{self.id}.webp"

class Group(Base):
    __tablename__ = "group"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False, index=True)
    description = Column(Text, nullable=True)
    cover_image = Column(String(1024), nullable=True)
    serial_number = Column(String(256), nullable=True, index=True)
    release_date = Column(Date, nullable=True)
    rating = Column(Integer, nullable=True)
    actor_id = Column(Integer, ForeignKey("actor.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 保留原有字段用于兼容
    size = Column(Integer, default=0)
    media_cnt = Column(Integer, default=0)

    # 关系
    actor = relationship("Actor", back_populates="groups")
    media = relationship("Media", back_populates="group")
    
    @property
    def thumbnail(self):
        return f"data/group_cover/{self.id}.webp"

class Media(Base):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)

    type = Column(Enum(MediaType), nullable=True)
    local_media_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(128), nullable=True, index=True)
    date = Column(Date, nullable=True)
    duration = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    rating = Column(Integer, nullable=True)
    view_count = Column(Integer, default=0, nullable=False)
    last_viewed_at = Column(DateTime, nullable=True)

    remote_media_url = Column(String(1024), default="", nullable=True)

    start_time = Column(Float, nullable=True)
    timestamp = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)

    actor_id = Column(Integer, ForeignKey("actor.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("group.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("media.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    parent = relationship("Media", remote_side=[id], backref=backref("previews", order_by="Media.start_time"))
    actor = relationship("Actor", back_populates="media")
    group = relationship("Group", back_populates="media")
    tags = relationship("Tagging", secondary="media_tags", back_populates="media")
    
    @property
    def remote_thumbnail_url(self):
        return f"/data/thumbs/{self.id}.webp"

class ActorTags(Base):
    __tablename__ = "actor_tags"
    actor_id = Column(Integer, ForeignKey("actor.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tagging.id"), primary_key=True)

class MediaTags(Base):
    __tablename__ = "media_tags"
    media_id = Column(Integer, ForeignKey("media.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tagging.id"), primary_key=True)

class Tagging(Base):
    __tablename__ = "tagging"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    category = Column(String(64), default='body', nullable=True)
    
    # 关系
    actors = relationship("Actor", secondary="actor_tags", back_populates="tags")
    media = relationship("Media", secondary="media_tags", back_populates="tags")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
