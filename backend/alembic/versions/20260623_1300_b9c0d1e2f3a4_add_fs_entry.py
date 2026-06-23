"""add fs_entry disk-scan index table

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-06-23 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9c0d1e2f3a4'
down_revision: Union[str, Sequence[str], None] = 'a8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 磁盘扫描索引表:反映文件系统物理真相,不去重(同内容两路径=两行)。
    # 唯一约束只有 (repo_id, rel_path) —— 与 media.file_hash UNIQUE 的本质差异。
    op.create_table(
        'fs_entry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_id', sa.String(length=64), nullable=False),
        sa.Column('rel_path', sa.String(length=1024), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('media_type', sa.String(length=16), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mtime', sa.Float(), nullable=False),
        sa.Column('scanned_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('media_id', sa.Integer(), nullable=True),
        sa.Column('meta_status', sa.String(length=16), nullable=False, server_default='pending'),
        sa.Column('thumb_status', sa.String(length=16), nullable=False, server_default='pending'),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('bitrate', sa.Integer(), nullable=True),
        sa.Column('video_codec', sa.String(length=32), nullable=True),
        sa.Column('audio_codec', sa.String(length=32), nullable=True),
        sa.Column('has_audio', sa.Integer(), nullable=True),
        sa.Column('taken_at', sa.DateTime(), nullable=True),
        sa.Column('gps_lat', sa.Float(), nullable=True),
        sa.Column('gps_lng', sa.Float(), nullable=True),
        sa.Column('orientation', sa.Integer(), nullable=True),
        sa.Column('camera_make', sa.String(length=64), nullable=True),
        sa.Column('camera_model', sa.String(length=64), nullable=True),
        sa.Column('lens', sa.String(length=128), nullable=True),
        sa.Column('is_hdr', sa.Integer(), nullable=True),
        sa.Column('color_transfer', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repo_id', 'rel_path', name='uq_fs_entry_repo_relpath'),
    )
    op.create_index(op.f('ix_fs_entry_id'), 'fs_entry', ['id'], unique=True)
    op.create_index('ix_fs_entry_mtime', 'fs_entry', ['mtime'])
    op.create_index('ix_fs_entry_file_size', 'fs_entry', ['file_size'])
    op.create_index('ix_fs_entry_repo_id', 'fs_entry', ['repo_id'])
    op.create_index('ix_fs_entry_media_id', 'fs_entry', ['media_id'])
    op.create_index('ix_fs_entry_meta_status', 'fs_entry', ['meta_status'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_fs_entry_meta_status', table_name='fs_entry')
    op.drop_index('ix_fs_entry_media_id', table_name='fs_entry')
    op.drop_index('ix_fs_entry_repo_id', table_name='fs_entry')
    op.drop_index('ix_fs_entry_file_size', table_name='fs_entry')
    op.drop_index('ix_fs_entry_mtime', table_name='fs_entry')
    op.drop_index(op.f('ix_fs_entry_id'), table_name='fs_entry')
    op.drop_table('fs_entry')
