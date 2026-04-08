"""rename_duration_to_duration_ms

Revision ID: 0388688167b2
Revises: 2e17e07d0ec6
Create Date: 2026-04-03 22:07:47.133280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0388688167b2'
down_revision: Union[str, Sequence[str], None] = '2e17e07d0ec6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 新数据库已经用 duration_ms 建表，无需 rename
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
