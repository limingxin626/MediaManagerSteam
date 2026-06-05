"""seed repositories.json

把"哪些目录是 repository"从 env vars (UPLOAD_DIR / STATIC_DIRS) 迁移到
`<DATA_ROOT>/repositories.json`。新机器手写这个文件;老机器跑这个 migration
会按 env vars 自动 seed 一份出来,平台 key 用 sys.platform 推断。

不动 DB schema,只是写文件。已有 repositories.json → 跳过。
downgrade no-op(JSON 文件保留,无害)。

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-06-05 21:00:00.000000
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Sequence, Union


revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


logger = logging.getLogger("alembic.seed_repositories_json")

REPOSITORIES_FILENAME = "repositories.json"


def _platform_key() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def _dir_name(path: str) -> str:
    return os.path.basename(os.path.normpath(path))


def upgrade() -> None:
    # 刻意不 import app.config,避开 ffmpeg 探活 + repositories.json fail-fast。
    data_root = (os.getenv("DATA_ROOT") or "").strip()
    if not data_root:
        logger.warning("[seed repositories.json] DATA_ROOT 未设置,跳过 seed")
        return
    data_root = os.path.abspath(data_root)

    target = os.path.join(data_root, REPOSITORIES_FILENAME)
    if os.path.isfile(target):
        logger.info("[seed repositories.json] %s 已存在,跳过", target)
        return

    upload_dir = (os.getenv("UPLOAD_DIR") or "").strip()
    static_dirs_raw = (os.getenv("STATIC_DIRS") or "").strip()
    if not upload_dir:
        logger.warning(
            "[seed repositories.json] UPLOAD_DIR 未设置,无法 seed。"
            "请在 %s 手写 repositories.json 后再启动 backend。",
            data_root,
        )
        return

    plat = _platform_key()
    abs_upload = os.path.abspath(upload_dir).replace("\\", "/")
    default_repo_id = _dir_name(upload_dir).lower()

    repos = {
        default_repo_id: {
            "human_name": _dir_name(upload_dir),
            "paths": {plat: abs_upload},
        }
    }
    for d in static_dirs_raw.split(";"):
        d = d.strip()
        if not d:
            continue
        abs_d = os.path.abspath(d).replace("\\", "/")
        rid = _dir_name(d).lower()
        if rid in repos:
            continue  # default repo 已存在,不覆盖
        repos[rid] = {
            "human_name": _dir_name(d),
            "paths": {plat: abs_d},
        }

    payload = {
        "version": 1,
        "default_repo_id": default_repo_id,
        "repositories": repos,
    }

    os.makedirs(data_root, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(
        "[seed repositories.json] 已 seed %s (%d repos,平台=%s): %s",
        target, len(repos), plat, list(repos.keys()),
    )
    logger.warning(
        "[seed repositories.json] 注意:只填了当前平台(%s)的路径。"
        "如要让 Mac/Windows 共享同一 DB,请手动补另一个平台的 paths 段。",
        plat,
    )


def downgrade() -> None:
    # no-op:JSON 文件保留无害。如真要清,用户手动 rm。
    pass
