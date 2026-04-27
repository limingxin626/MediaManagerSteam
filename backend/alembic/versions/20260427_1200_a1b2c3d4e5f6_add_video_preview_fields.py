"""add_video_preview_fields

在 media 表上加用户标记的视频预览字段（章节）：
- video_media_id：所属视频 media id（self FK，CASCADE）
- frame_ms / start_ms / end_ms：预览帧时刻 + 可选区间
顺带把 file_hash 的 unique 约束改为普通索引，以允许同一图片文件在不同视频独占预览语义下产生多行 Media。

Revision ID: a1b2c3d4e5f6
Revises: dd558fd0f564
Create Date: 2026-04-27 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'dd558fd0f564'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('media') as batch_op:
        batch_op.add_column(sa.Column('video_media_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('frame_ms', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('start_ms', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('end_ms', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_media_video_media_id', 'media',
            ['video_media_id'], ['id'], ondelete='CASCADE'
        )
        batch_op.create_index('ix_media_video_media_id', ['video_media_id'])
        batch_op.create_index('ix_media_video_frame', ['video_media_id', 'frame_ms'])

    # 把 file_hash 的唯一索引改为普通索引（同名重建）。
    # 用独立 batch 块以便单独失败时不影响上面的列添加。
    try:
        with op.batch_alter_table('media') as batch_op:
            batch_op.drop_index('ix_media_file_hash')
    except Exception:
        pass
    with op.batch_alter_table('media') as batch_op:
        batch_op.create_index('ix_media_file_hash', ['file_hash'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('media') as batch_op:
        batch_op.drop_index('ix_media_video_frame')
        batch_op.drop_index('ix_media_video_media_id')
        batch_op.drop_constraint('fk_media_video_media_id', type_='foreignkey')
        batch_op.drop_column('end_ms')
        batch_op.drop_column('start_ms')
        batch_op.drop_column('frame_ms')
        batch_op.drop_column('video_media_id')

    try:
        with op.batch_alter_table('media') as batch_op:
            batch_op.drop_index('ix_media_file_hash')
    except Exception:
        pass
    with op.batch_alter_table('media') as batch_op:
        batch_op.create_index('ix_media_file_hash', ['file_hash'], unique=True)
