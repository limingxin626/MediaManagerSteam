"""persist folder classification kind

Revision ID: c1d2e3f4a5b6
Revises: b6c7d8e9f0a1
Create Date: 2026-08-25
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b6c7d8e9f0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("folder")}
    if "kind" not in columns:
        op.add_column(
            "folder",
            sa.Column(
                "kind",
                sa.String(length=32),
                nullable=False,
                server_default="unknown",
            ),
        )
    indexes = {index["name"] for index in inspector.get_indexes("folder")}
    if "ix_folder_kind" not in indexes:
        op.create_index("ix_folder_kind", "folder", ["kind"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("folder")}
    if "ix_folder_kind" in indexes:
        op.drop_index("ix_folder_kind", table_name="folder")
    columns = {column["name"] for column in inspector.get_columns("folder")}
    if "kind" in columns:
        op.drop_column("folder", "kind")
