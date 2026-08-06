"""replace fs_entry with repository catalog

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-08-06 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repository_folder",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repo_id", sa.String(length=64), nullable=False),
        sa.Column("rel_path", sa.String(length=1024), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("scanned_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["repository_folder.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id", "rel_path", name="uq_repository_folder_repo_path"),
    )
    op.create_index(op.f("ix_repository_folder_id"), "repository_folder", ["id"], unique=True)
    op.create_index(op.f("ix_repository_folder_parent_id"), "repository_folder", ["parent_id"])
    op.create_index("ix_repository_folder_repo_parent", "repository_folder", ["repo_id", "parent_id"])

    op.create_table(
        "repository_file",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repo_id", sa.String(length=64), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=False),
        sa.Column("rel_path", sa.String(length=1024), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("media_type", sa.String(length=16), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mtime", sa.Float(), nullable=False),
        sa.Column("scanned_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=True),
        sa.Column("materialize_status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("materialize_error", sa.String(length=512), nullable=True),
        sa.Column("is_hdr", sa.Integer(), nullable=True),
        sa.Column("color_transfer", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["folder_id"], ["repository_folder.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id", "rel_path", name="uq_repository_file_repo_path"),
    )
    op.create_index(op.f("ix_repository_file_id"), "repository_file", ["id"], unique=True)
    op.create_index(op.f("ix_repository_file_folder_id"), "repository_file", ["folder_id"])
    op.create_index(op.f("ix_repository_file_media_id"), "repository_file", ["media_id"])
    op.create_index("ix_repository_file_repo_folder_name", "repository_file", ["repo_id", "folder_id", "name"])
    op.create_index("ix_repository_file_repo_mtime", "repository_file", ["repo_id", "mtime"])
    op.create_index("ix_repository_file_materialize", "repository_file", ["materialize_status", "id"])

    # Existing fs_entry data is deliberately not copied: it did not represent folders,
    # and a fresh scan is required to build consistent parent relationships.
    op.drop_table("fs_entry")


def downgrade() -> None:
    op.create_table(
        "fs_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repo_id", sa.String(length=64), nullable=False),
        sa.Column("rel_path", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("media_type", sa.String(length=16), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mtime", sa.Float(), nullable=False),
        sa.Column("scanned_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=True),
        sa.Column("meta_status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("thumb_status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("width", sa.Integer()), sa.Column("height", sa.Integer()),
        sa.Column("duration_ms", sa.Integer()), sa.Column("fps", sa.Float()),
        sa.Column("bitrate", sa.Integer()), sa.Column("video_codec", sa.String(length=32)),
        sa.Column("audio_codec", sa.String(length=32)), sa.Column("has_audio", sa.Integer()),
        sa.Column("taken_at", sa.DateTime()), sa.Column("gps_lat", sa.Float()),
        sa.Column("gps_lng", sa.Float()), sa.Column("orientation", sa.Integer()),
        sa.Column("camera_make", sa.String(length=64)), sa.Column("camera_model", sa.String(length=64)),
        sa.Column("lens", sa.String(length=128)), sa.Column("is_hdr", sa.Integer()),
        sa.Column("color_transfer", sa.String(length=32)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_id", "rel_path", name="uq_fs_entry_repo_relpath"),
    )
    op.create_index("ix_fs_entry_mtime", "fs_entry", ["mtime"])
    op.create_index("ix_fs_entry_file_size", "fs_entry", ["file_size"])
    op.create_index("ix_fs_entry_repo_id", "fs_entry", ["repo_id"])
    op.create_index("ix_fs_entry_media_id", "fs_entry", ["media_id"])
    op.create_index("ix_fs_entry_meta_status", "fs_entry", ["meta_status"])
    op.create_index(op.f("ix_fs_entry_id"), "fs_entry", ["id"], unique=True)

    op.drop_table("repository_file")
    op.drop_table("repository_folder")
