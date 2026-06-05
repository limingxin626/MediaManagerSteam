"""media repo_id

把 media.file_path 从「写入时机器上的绝对路径」改成「相对挂载根的相对路径」,
新增 repo_id 列标识挂在哪个 mount 上。

upgrade 三步:
  1. 加 nullable repo_id 列
  2. backfill —— 按最长 mount 前缀匹配,重写 file_path 为相对路径
  3. 收紧 nullable + server_default + 索引

downgrade 把相对路径还原成绝对路径,drop 列。

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-06-06 12:00:00.000000
"""
from __future__ import annotations

import logging
import os
from typing import Dict, Sequence, Tuple, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


logger = logging.getLogger("alembic.media_repo_id")


# --------------------------------------------------------------------------- #
# 直接读 env 重建 mount 表,刻意不 import app.config —— config 在启动时会跑 ffmpeg 探活,
# 在 alembic 上下文里调用会 sys.exit。
# --------------------------------------------------------------------------- #

def _dir_name(path: str) -> str:
    return os.path.basename(os.path.normpath(path))


def _load_mounts_from_env() -> Dict[str, str]:
    """{repo_id: abs_mount_path}。UPLOAD_DIR + STATIC_DIRS 全用 basename.lower() 作 id。"""
    upload_dir = (os.getenv("UPLOAD_DIR") or "").strip()
    static_dirs_raw = (os.getenv("STATIC_DIRS") or "").strip()

    repos: Dict[str, str] = {}
    if upload_dir:
        abs_upload = os.path.abspath(upload_dir)
        repos[_dir_name(abs_upload).lower()] = abs_upload
    for d in static_dirs_raw.split(";"):
        d = d.strip()
        if not d:
            continue
        abs_d = os.path.abspath(d)
        repos[_dir_name(abs_d).lower()] = abs_d
    return repos


def _classify(abs_path: str, mounts: Dict[str, str]) -> Tuple[str, str]:
    """绝对路径 → (repo_id, forward-slash 相对路径)。

    按 mount 路径长度 DESC 匹配(嵌套 mount 时长的赢)。未命中返回 ("__legacy__", 原 abs_path)。
    """
    if not abs_path:
        return "__legacy__", abs_path
    norm = abs_path.replace("\\", "/")
    norm_lc = norm.lower()
    candidates = sorted(mounts.items(), key=lambda kv: len(kv[1]), reverse=True)
    for rid, mount in candidates:
        mount_norm = mount.replace("\\", "/").rstrip("/")
        mount_lc = mount_norm.lower()
        if norm_lc == mount_lc:
            return rid, ""
        if norm_lc.startswith(mount_lc + "/"):
            rel = norm[len(mount_norm):].lstrip("/")
            return rid, rel
    return "__legacy__", abs_path


def _reconstruct(repo_id: str, rel: str, mounts: Dict[str, str]) -> str:
    """downgrade 用:repo_id + 相对路径 → 本机绝对路径。"""
    if repo_id == "__legacy__":
        return rel  # 已经是绝对的
    mount = mounts.get(repo_id)
    if not mount:
        return rel  # repo 现在不存在,留原样(可能不可读,但不影响 downgrade 完成)
    if not rel:
        return mount
    return os.path.join(mount, rel.replace("/", os.sep))


# --------------------------------------------------------------------------- #
# upgrade / downgrade
# --------------------------------------------------------------------------- #

def upgrade() -> None:
    # 1. 加 nullable 列
    with op.batch_alter_table('media') as batch_op:
        batch_op.add_column(sa.Column('repo_id', sa.String(length=64), nullable=True))

    # 2. backfill
    mounts = _load_mounts_from_env()
    if not mounts:
        logger.warning(
            "[media repo migration] 既无 UPLOAD_DIR 也无 STATIC_DIRS,"
            "所有 media 将被标记 __legacy__,file_path 保持绝对路径"
        )

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, file_path FROM media")).fetchall()
    counts: Dict[str, int] = {}
    for row in rows:
        repo_id, rel = _classify(row.file_path, mounts)
        counts[repo_id] = counts.get(repo_id, 0) + 1
        if repo_id == "__legacy__":
            logger.warning(
                "[media repo migration] orphan id=%s path=%s",
                row.id, row.file_path
            )
        conn.execute(
            sa.text("UPDATE media SET repo_id=:r, file_path=:p WHERE id=:i"),
            {"r": repo_id, "p": rel, "i": row.id},
        )
    logger.info("[media repo migration] backfill 完成: %s", counts)

    # 3. 收紧 nullable + 默认值 + 索引
    with op.batch_alter_table('media') as batch_op:
        batch_op.alter_column(
            'repo_id',
            existing_type=sa.String(length=64),
            nullable=False,
            server_default='uploads',  # 仅作 belt-and-suspenders;新代码总是显式写
        )
    op.create_index('ix_media_repo_id', 'media', ['repo_id'])


def downgrade() -> None:
    mounts = _load_mounts_from_env()
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, repo_id, file_path FROM media")).fetchall()
    for row in rows:
        abs_path = _reconstruct(row.repo_id, row.file_path or "", mounts)
        conn.execute(
            sa.text("UPDATE media SET file_path=:p WHERE id=:i"),
            {"p": abs_path, "i": row.id},
        )
    op.drop_index('ix_media_repo_id', table_name='media')
    with op.batch_alter_table('media') as batch_op:
        batch_op.drop_column('repo_id')
