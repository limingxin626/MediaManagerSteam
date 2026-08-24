"""Repository filesystem catalog models.

The catalog records physical paths independently from Media's deduplicated logical
assets. Physically empty directories are intentionally omitted.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Table, UniqueConstraint, text
from sqlalchemy.orm import relationship

from app.models import Base


folder_tag = Table(
    "folder_tag",
    Base.metadata,
    Column("folder_id", Integer, ForeignKey("folder.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)


class Folder(Base):
    __tablename__ = "folder"

    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("collection.id", ondelete="SET NULL"), nullable=True, index=True)
    issue_id = Column(Integer, ForeignKey("issue.id", ondelete="SET NULL"), nullable=True, index=True)
    starred = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    collection = relationship("Collection", back_populates="folders")
    issue = relationship("Issue", back_populates="folders")
    locations = relationship("FolderLocation", back_populates="folder", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=folder_tag, back_populates="folders")


class FolderLocation(Base):
    __tablename__ = "folder_location"

    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("folder.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_folder_id = Column(
        Integer,
        ForeignKey("repository_folder.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    role = Column(String(16), nullable=False, default="PRIMARY", server_default="PRIMARY")
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    folder = relationship("Folder", back_populates="locations")
    repository_folder = relationship("RepositoryFolder", back_populates="folder_location")

    __table_args__ = (
        Index(
            "uq_folder_location_primary",
            "folder_id",
            unique=True,
            sqlite_where=text("role = 'PRIMARY'"),
        ),
    )


class RepositoryFolder(Base):
    __tablename__ = "repository_folder"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(String(64), nullable=False)
    filesystem_id = Column(String(128), nullable=True)
    rel_path = Column(String(1024), nullable=False)  # "" is the repository root
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("repository_folder.id", ondelete="CASCADE"), nullable=True, index=True)
    scanned_at = Column(DateTime, default=datetime.now, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    parent = relationship("RepositoryFolder", remote_side="RepositoryFolder.id", back_populates="children")
    children = relationship("RepositoryFolder", back_populates="parent", cascade="all, delete-orphan", passive_deletes=True)
    files = relationship("RepositoryFile", back_populates="folder", cascade="all, delete-orphan", passive_deletes=True)
    message_link = relationship("MessageFolder", back_populates="folder", cascade="all, delete-orphan", uselist=False)
    folder_location = relationship(
        "FolderLocation",
        back_populates="repository_folder",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint("repo_id", "rel_path", name="uq_repository_folder_repo_path"),
        UniqueConstraint("repo_id", "filesystem_id", name="uq_repository_folder_repo_filesystem_id"),
        Index("ix_repository_folder_repo_parent", "repo_id", "parent_id"),
    )


class MessageFolder(Base):
    __tablename__ = "message_folder"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("message.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_folder_id = Column(
        Integer,
        ForeignKey("repository_folder.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    role = Column(String(16), nullable=False, default="PRIMARY", server_default="PRIMARY")
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    message = relationship("Message", back_populates="folder_links")
    folder = relationship("RepositoryFolder", back_populates="message_link")

    __table_args__ = (
        Index(
            "uq_message_folder_primary",
            "message_id",
            unique=True,
            sqlite_where=text("role = 'PRIMARY'"),
        ),
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
