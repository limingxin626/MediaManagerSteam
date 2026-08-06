"""add media file creation time

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-08-06 15:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("media", sa.Column("file_created_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_media_file_created_at"), "media", ["file_created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_media_file_created_at"), table_name="media")
    op.drop_column("media", "file_created_at")
