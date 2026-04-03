from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = "sqlite:///./db_new.sqlite3"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

message_tag = Table(
    'message_tag',
    Base.metadata,
    Column('message_id', Integer, ForeignKey('message.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True)
)

class Message(Base):
    __tablename__ = "message"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=True)
    actor_id = Column(Integer, ForeignKey("actor.id"), nullable=True, index=True)
    starred = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    actor = relationship("Actor", back_populates="messages")
    message_media = relationship("MessageMedia", back_populates="message", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=message_tag, back_populates="messages")

class Actor(Base):
    __tablename__ = "actor"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False, index=True)
    description = Column(Text, nullable=True)
    avatar_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    messages = relationship("Message", back_populates="actor")

class Tag(Base):
    __tablename__ = "tag"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False, index=True)
    category = Column(String(128), nullable=True, index=True)
    
    messages = relationship("Message", secondary=message_tag, back_populates="tags")

class Media(Base):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(255), nullable=False)
    file_hash = Column(String(128), nullable=True, index=True, unique=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    rating = Column(Integer, default=0, nullable=False)
    starred = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    last_viewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    message_media = relationship("MessageMedia", back_populates="media")

class MessageMedia(Base):
    __tablename__ = "message_media"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("message.id"), nullable=False, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    message = relationship("Message", back_populates="message_media")
    media = relationship("Media", back_populates="message_media")


class SyncLog(Base):
    __tablename__ = "sync_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(32), nullable=False)   # MESSAGE | ACTOR | MEDIA | TAG
    entity_id = Column(Integer, nullable=False)
    operation = Column(String(16), nullable=False)      # UPSERT | DELETE
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_sync_log_timestamp_id", "timestamp", "id"),
        Index("ix_sync_log_entity", "entity_type", "entity_id"),
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()