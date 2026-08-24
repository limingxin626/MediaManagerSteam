"""add independent folder domain

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-08-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b6c7d8e9f0a1"
down_revision: Union[str, Sequence[str], None] = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())

    if "folder" not in tables:
        op.create_table(
            "folder",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("collection_id", sa.Integer(), nullable=True),
            sa.Column("issue_id", sa.Integer(), nullable=True),
            sa.Column("starred", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["collection_id"], ["collection.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["issue_id"], ["issue.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_folder_collection_id", "folder", ["collection_id"])
        op.create_index("ix_folder_created_at", "folder", ["created_at"])
        op.create_index("ix_folder_id", "folder", ["id"])
        op.create_index("ix_folder_issue_id", "folder", ["issue_id"])

    if "folder_tag" not in tables:
        op.create_table(
            "folder_tag",
            sa.Column("folder_id", sa.Integer(), nullable=False),
            sa.Column("tag_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["folder_id"], ["folder.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tag_id"], ["tag.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("folder_id", "tag_id"),
        )

    if "folder_location" not in tables:
        op.create_table(
            "folder_location",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("folder_id", sa.Integer(), nullable=False),
            sa.Column("repository_folder_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(length=16), server_default="PRIMARY", nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["folder_id"], ["folder.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["repository_folder_id"], ["repository_folder.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_folder_location_folder_id", "folder_location", ["folder_id"])
        op.create_index("ix_folder_location_id", "folder_location", ["id"])
        op.create_index(
            "ix_folder_location_repository_folder_id",
            "folder_location",
            ["repository_folder_id"],
            unique=True,
        )
        op.create_index(
            "uq_folder_location_primary",
            "folder_location",
            ["folder_id"],
            unique=True,
            sqlite_where=sa.text("role = 'PRIMARY'"),
        )

    tables = set(sa.inspect(bind).get_table_names())
    if "message_folder" not in tables:
        return

    bind.execute(sa.text("""
        INSERT OR IGNORE INTO folder
            (id, collection_id, issue_id, starred, created_at, updated_at)
        SELECT m.id, m.collection_id, m.issue_id, m.starred, m.created_at, m.updated_at
        FROM message AS m
        JOIN (SELECT DISTINCT message_id FROM message_folder) AS linked
          ON linked.message_id = m.id
    """))
    bind.execute(sa.text("""
        INSERT OR IGNORE INTO folder_location
            (folder_id, repository_folder_id, role, created_at)
        SELECT message_id, repository_folder_id, role, created_at
        FROM message_folder
    """))
    bind.execute(sa.text("""
        INSERT OR IGNORE INTO folder_tag (folder_id, tag_id)
        SELECT mt.message_id, mt.tag_id
        FROM message_tag AS mt
        JOIN message_folder AS mf ON mf.message_id = mt.message_id
    """))
    bind.execute(sa.text("""
        DELETE FROM message_media
        WHERE message_id IN (SELECT DISTINCT message_id FROM message_folder)
    """))
    bind.execute(sa.text("""
        DELETE FROM message_tag
        WHERE message_id IN (SELECT DISTINCT message_id FROM message_folder)
    """))
    bind.execute(sa.text("""
        DELETE FROM message
        WHERE id IN (SELECT DISTINCT message_id FROM message_folder)
    """))


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "folder_location" in tables:
        op.drop_table("folder_location")
    if "folder_tag" in tables:
        op.drop_table("folder_tag")
    if "folder" in tables:
        op.drop_table("folder")