"""media_file_hash_unique

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-05-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dupes = bind.execute(sa.text(
        "SELECT file_hash, COUNT(*) c FROM media "
        "WHERE file_hash IS NOT NULL GROUP BY file_hash HAVING c > 1"
    )).fetchall()
    if dupes:
        sample = ", ".join(f"{r[0][:12]}…(x{r[1]})" for r in dupes[:5])
        raise RuntimeError(
            f"无法创建 media.file_hash 唯一索引:存在 {len(dupes)} 组重复哈希。"
            f"请先在应用内合并这些 Media 行,再重试 migration。示例:{sample}"
        )

    with op.batch_alter_table('media') as batch_op:
        batch_op.drop_index('ix_media_file_hash')
        batch_op.create_index('ix_media_file_hash', ['file_hash'], unique=True)


def downgrade() -> None:
    with op.batch_alter_table('media') as batch_op:
        batch_op.drop_index('ix_media_file_hash')
        batch_op.create_index('ix_media_file_hash', ['file_hash'], unique=False)
