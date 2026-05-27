"""add_message_fts

Revision ID: a7b8c9d0e1f2
Revises: 5f1a2b3c4d5e
Create Date: 2026-05-26 11:00:00.000000

为 message.text 建立 FTS5 全文索引（external content 表，不复制正文），
并通过 triggers 与 message 表保持同步。
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = '5f1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE VIRTUAL TABLE message_fts USING fts5(
            text,
            content='message',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        )
    """)

    op.execute("""
        INSERT INTO message_fts(rowid, text)
        SELECT id, text FROM message WHERE text IS NOT NULL
    """)

    op.execute("""
        CREATE TRIGGER message_fts_ai AFTER INSERT ON message BEGIN
            INSERT INTO message_fts(rowid, text) VALUES (new.id, new.text);
        END
    """)
    op.execute("""
        CREATE TRIGGER message_fts_ad AFTER DELETE ON message BEGIN
            INSERT INTO message_fts(message_fts, rowid, text) VALUES('delete', old.id, old.text);
        END
    """)
    op.execute("""
        CREATE TRIGGER message_fts_au AFTER UPDATE OF text ON message BEGIN
            INSERT INTO message_fts(message_fts, rowid, text) VALUES('delete', old.id, old.text);
            INSERT INTO message_fts(rowid, text) VALUES (new.id, new.text);
        END
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS message_fts_au")
    op.execute("DROP TRIGGER IF EXISTS message_fts_ad")
    op.execute("DROP TRIGGER IF EXISTS message_fts_ai")
    op.execute("DROP TABLE IF EXISTS message_fts")
