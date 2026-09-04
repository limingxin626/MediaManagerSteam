"""add folder_person (folder ↔ people many-to-many)

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-08-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "folder_person" not in inspector.get_table_names():
        op.create_table(
            "folder_person",
            sa.Column("folder_id", sa.Integer(), nullable=False),
            sa.Column("person_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["folder_id"], ["folder.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["person_id"], ["person.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("folder_id", "person_id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "folder_person" in inspector.get_table_names():
        op.drop_table("folder_person")
