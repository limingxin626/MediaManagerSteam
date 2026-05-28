"""media exif fields

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-05-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, Sequence[str], None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_COLS = [
    ('taken_at', sa.DateTime(), True),
    ('gps_lat', sa.Float(), True),
    ('gps_lng', sa.Float(), True),
    ('orientation', sa.Integer(), True),
    ('camera_make', sa.String(length=64), True),
    ('camera_model', sa.String(length=64), True),
    ('lens', sa.String(length=128), True),
    ('video_codec', sa.String(length=32), True),
    ('audio_codec', sa.String(length=32), True),
    ('has_audio', sa.Integer(), True),
    ('fps', sa.Float(), True),
    ('bitrate', sa.Integer(), True),
]


def upgrade() -> None:
    with op.batch_alter_table('media') as batch_op:
        for name, type_, nullable in NEW_COLS:
            batch_op.add_column(sa.Column(name, type_, nullable=nullable))
    op.create_index('ix_media_taken_at', 'media', ['taken_at'])


def downgrade() -> None:
    op.drop_index('ix_media_taken_at', table_name='media')
    with op.batch_alter_table('media') as batch_op:
        for name, _, _ in NEW_COLS:
            batch_op.drop_column(name)
