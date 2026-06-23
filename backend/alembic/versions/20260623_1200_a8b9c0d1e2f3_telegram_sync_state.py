"""add telegram sync state and remote media reference

Revision ID: a8b9c0d1e2f3
Revises: 865aca0da8ff
Create Date: 2026-06-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8b9c0d1e2f3'
down_revision: Union[str, Sequence[str], None] = '865aca0da8ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Telegram "Saved Messages" 同步的单行状态表。
    # 应用代码用 INSERT OR IGNORE (id=1) seed;不强制 db 层唯一(单行是约定)。
    op.create_table(
        'telegram_sync_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('last_message_id', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('total_imported', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_flood_wait_until', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # 远端未下载文件的引用表:media_id 是已入库的缩略图,原文件留在 telegram 等远端。
    # source_url 给人类看(浏览器能打开),source_msg_id 给程序化下载用。
    op.create_table(
        'remote_media_reference',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=32), nullable=False, server_default='telegram'),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('source_msg_id', sa.Integer(), nullable=False),
        sa.Column('source_chat_id', sa.Integer(), nullable=True),
        sa.Column('original_filename', sa.String(length=512), nullable=True),
        sa.Column('original_size', sa.Integer(), nullable=True),
        sa.Column('original_mime', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('media_id', name='uq_remote_ref_media_id'),
        sa.ForeignKeyConstraint(['media_id'], ['media.id'], name='fk_remote_ref_media_id'),
    )
    op.create_index(op.f('ix_remote_media_reference_id'), 'remote_media_reference', ['id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_remote_media_reference_id'), table_name='remote_media_reference')
    op.drop_table('remote_media_reference')
    op.drop_table('telegram_sync_state')