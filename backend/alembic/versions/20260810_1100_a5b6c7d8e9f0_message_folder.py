"""current schema baseline

Revision ID: a5b6c7d8e9f0
Revises:
Create Date: 2026-08-14

This project supports either a fresh database or an existing database already
stamped at this revision. Older incremental migrations were squashed into this
baseline.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import Base

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app.models import Base

    Base.metadata.drop_all(bind=op.get_bind())
