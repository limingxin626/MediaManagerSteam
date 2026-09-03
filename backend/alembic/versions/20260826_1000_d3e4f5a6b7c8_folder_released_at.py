"""add folder.released_at (发行日期)

Revision ID: d3e4f5a6b7c8
Revises: c1d2e3f4a5b6
Create Date: 2026-08-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("folder")}
    if "released_at" not in columns:
        op.add_column(
            "folder",
            sa.Column("released_at", sa.DateTime(), nullable=True),
        )
    indexes = {index["name"] for index in inspector.get_indexes("folder")}
    if "ix_folder_released_at" not in indexes:
        op.create_index("ix_folder_released_at", "folder", ["released_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("folder")}
    if "ix_folder_released_at" in indexes:
        op.drop_index("ix_folder_released_at", table_name="folder")
    columns = {column["name"] for column in inspector.get_columns("folder")}
    if "released_at" in columns:
        op.drop_column("folder", "released_at")
