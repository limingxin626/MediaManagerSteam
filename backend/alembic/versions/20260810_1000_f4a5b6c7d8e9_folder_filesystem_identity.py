"""add stable repository folder filesystem identity

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-08-10 10:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, Sequence[str], None] = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("repository_folder") as batch_op:
        batch_op.add_column(sa.Column("filesystem_id", sa.String(length=128), nullable=True))
        batch_op.create_unique_constraint(
            "uq_repository_folder_repo_filesystem_id",
            ["repo_id", "filesystem_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("repository_folder") as batch_op:
        batch_op.drop_constraint("uq_repository_folder_repo_filesystem_id", type_="unique")
        batch_op.drop_column("filesystem_id")