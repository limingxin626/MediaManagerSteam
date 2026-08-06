"""Repository filesystem catalog models.

The catalog records physical paths independently from Media's deduplicated logical
assets. Folders are first-class rows so empty directories remain browsable.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models import Base


class RepositoryFolder(Base):
    __tablename__ = "repository_folder"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(String(64), nullable=False)
    rel_path = Column(String(1024), nullable=False)  # "" is the repository root
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("repository_folder.id", ondelete="CASCADE"), nullable=True, index=True)
    scanned_at = Column(DateTime, default=datetime.now, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    parent = relationship("RepositoryFolder", remote_side="RepositoryFolder.id", back_populates="children")
    children = relationship("RepositoryFolder", back_populates="parent", cascade="all, delete-orphan", passive_deletes=True)
    files = relationship("RepositoryFile", back_populates="folder", cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("repo_id", "rel_path", name="uq_repository_folder_repo_path"),
        Index("ix_repository_folder_repo_parent", "repo_id", "parent_id"),
    )


class RepositoryFile(Base):
    __tablename__ = "repository_file"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(String(64), nullable=False)
    folder_id = Column(Integer, ForeignKey("repository_folder.id", ondelete="CASCADE"), nullable=False, index=True)
    rel_path = Column(String(1024), nullable=False)
    name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    media_type = Column(String(16), nullable=False)
    file_size = Column(Integer, nullable=True)
    mtime = Column(Float, nullable=False)
    scanned_at = Column(DateTime, default=datetime.now, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    media_id = Column(Integer, ForeignKey("media.id", ondelete="SET NULL"), nullable=True, index=True)
    materialize_status = Column(String(16), nullable=False, default="pending", server_default="pending")
    materialize_error = Column(String(512), nullable=True)
    is_hdr = Column(Integer, nullable=True)
    color_transfer = Column(String(32), nullable=True)

    folder = relationship("RepositoryFolder", back_populates="files")
    media = relationship("Media")

    __table_args__ = (
        UniqueConstraint("repo_id", "rel_path", name="uq_repository_file_repo_path"),
        Index("ix_repository_file_repo_folder_name", "repo_id", "folder_id", "name"),
        Index("ix_repository_file_repo_mtime", "repo_id", "mtime"),
        Index("ix_repository_file_materialize", "materialize_status", "id"),
    )
