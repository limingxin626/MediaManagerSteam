"""add_media_embedding

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-05-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'media_embedding',
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.Column('model', sa.String(length=64), nullable=False),
        sa.Column('vector', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['media_id'], ['media.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('media_id'),
    )


def downgrade() -> None:
    op.drop_table('media_embedding')
