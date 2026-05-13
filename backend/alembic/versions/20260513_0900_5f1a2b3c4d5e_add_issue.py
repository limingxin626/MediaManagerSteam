"""add_issue

Revision ID: 5f1a2b3c4d5e
Revises: 4d40c4acab1e
Create Date: 2026-05-13 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5f1a2b3c4d5e'
down_revision: Union[str, Sequence[str], None] = '4d40c4acab1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'issue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_issue_id'), 'issue', ['id'], unique=False)
    op.create_index(op.f('ix_issue_status'), 'issue', ['status'], unique=False)
    op.create_index('ix_issue_status_position', 'issue', ['status', 'position'], unique=False)

    with op.batch_alter_table('message') as batch_op:
        batch_op.add_column(sa.Column('issue_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_message_issue_id', ['issue_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_message_issue_id',
            'issue',
            ['issue_id'], ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    with op.batch_alter_table('message') as batch_op:
        batch_op.drop_constraint('fk_message_issue_id', type_='foreignkey')
        batch_op.drop_index('ix_message_issue_id')
        batch_op.drop_column('issue_id')

    op.drop_index('ix_issue_status_position', table_name='issue')
    op.drop_index(op.f('ix_issue_status'), table_name='issue')
    op.drop_index(op.f('ix_issue_id'), table_name='issue')
    op.drop_table('issue')
