"""rename actor to collection + add person / media_person

Revision ID: c1d2e3f4a5b6
Revises: b9c0d1e2f3a4
Create Date: 2026-07-16 19:30:00.000000

Actor(演员,与 message 一对多)重命名为 Collection(合集),语义调整;
新增 Person(人物)+ media_person 多对多(类似 Mac 相册人物,标注在 media 上)。
现有 actor 数据迁移保留(表改名 + avatar_path→cover_path 列改名 + message.actor_id→collection_id FK)。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b9c0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. actor 表 → collection,并把 avatar_path 列改名为 cover_path
    op.rename_table('actor', 'collection')
    with op.batch_alter_table('collection', schema=None) as batch_op:
        batch_op.alter_column('avatar_path', new_column_name='cover_path')

    # 2. message.actor_id → collection_id,FK 重新指向 collection.id
    #    batch_alter_table 在 SQLite 上走 copy-and-move,自动重建表与 FK。
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.alter_column('actor_id', new_column_name='collection_id')

    # 3. sync_log 历史行 entity_type='ACTOR' → 'COLLECTION'
    op.execute("UPDATE sync_log SET entity_type='COLLECTION' WHERE entity_type='ACTOR'")

    # 4. 新增 person 表
    op.create_table(
        'person',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_path', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_person_name'),
    )
    op.create_index('ix_person_id', 'person', ['id'], unique=False)
    op.create_index('ix_person_name', 'person', ['name'], unique=False)

    # 5. 新增 media_person 多对多 junction
    op.create_table(
        'media_person',
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['media_id'], ['media.id'], ),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
        sa.PrimaryKeyConstraint('media_id', 'person_id'),
    )


def downgrade() -> None:
    op.drop_table('media_person')
    op.drop_index('ix_person_name', table_name='person')
    op.drop_index('ix_person_id', table_name='person')
    op.drop_table('person')

    op.execute("UPDATE sync_log SET entity_type='ACTOR' WHERE entity_type='COLLECTION'")

    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.alter_column('collection_id', new_column_name='actor_id')

    with op.batch_alter_table('collection', schema=None) as batch_op:
        batch_op.alter_column('cover_path', new_column_name='avatar_path')
    op.rename_table('collection', 'actor')
