"""add message to repository folder mapping

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-08-10 11:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_folder",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("repository_folder_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), server_default="PRIMARY", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["message.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_folder_id"], ["repository_folder.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_folder_id"),
    )
    op.create_index(op.f("ix_message_folder_id"), "message_folder", ["id"], unique=True)
    op.create_index(op.f("ix_message_folder_message_id"), "message_folder", ["message_id"])
    op.create_index(
        op.f("ix_message_folder_repository_folder_id"),
        "message_folder",
        ["repository_folder_id"],
        unique=True,
    )
    op.create_index(
        "uq_message_folder_primary",
        "message_folder",
        ["message_id"],
        unique=True,
        sqlite_where=sa.text("role = 'PRIMARY'"),
    )


def downgrade() -> None:
    op.drop_table("message_folder")