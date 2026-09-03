"""Backfill ``Folder.released_at`` (发行日期) from Kodi-style ``.nfo`` files.

每个目录通常存一部作品,目录内放同名的 ``<NAME>.nfo``(如 ``SNIS-752/SNIS-752.nfo``),
内含 ``<release>2016-10-15</release>`` / ``<premiered>2016-10-15</premiered>``。
本脚本以逻辑 Folder 的 PRIMARY 物理目录为准,读其下 ``*.nfo`` 提取发行日期写回。

默认 dry-run(只打印将发生的变更),加 ``--apply`` 才写库。写库前自动备份 DB。
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import config
from app.models import Folder, FolderLocation, RepositoryFolder, SessionLocal

DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d")
RELEASE_TAGS = ("release", "premiered", "releasedate")


def backup_database(db_path: str) -> str:
    import sqlite3
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{db_path}.pre-released-at-{timestamp}.bak"
    source = sqlite3.connect(db_path)
    try:
        backup = sqlite3.connect(backup_path)
        try:
            source.backup(backup)
        finally:
            backup.close()
    finally:
        source.close()
    return backup_path


def _parse_date(text: str):
    text = (text or "").strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def extract_release_date(nfo_path: str):
    """读 nfo 里第一个 <release>/<premiered> 文本,解析为日期;失败返回 None。"""
    try:
        root = ET.parse(nfo_path).getroot()
    except (ET.ParseError, OSError):
        return None
    for tag in RELEASE_TAGS:
        for element in root.iter(tag):
            parsed = _parse_date(element.text)
            if parsed is not None:
                return parsed
    return None


def backfill_folder_released_at(
    apply: bool = False,
    repo: str | None = None,
    overwrite: bool = False,
) -> dict:
    db = SessionLocal()
    stats = {
        "folders": 0,
        "unresolved_location": 0,
        "missing_dir": 0,
        "no_nfo": 0,
        "nfo_parse_fail": 0,
        "set": 0,
        "changed": 0,
        "skipped_existing": 0,
        "samples": [],
    }
    try:
        rows = (
            db.query(Folder, FolderLocation, RepositoryFolder)
            .join(FolderLocation, FolderLocation.folder_id == Folder.id)
            .join(RepositoryFolder, RepositoryFolder.id == FolderLocation.repository_folder_id)
            .filter(FolderLocation.role == "PRIMARY")
            .order_by(Folder.id)
            .all()
        )
        if repo:
            rows = [row for row in rows if row[2].repo_id == repo]
        seen_folder_ids: set[int] = set()
        for folder, _location, physical in rows:
            if folder.id in seen_folder_ids:
                continue
            seen_folder_ids.add(folder.id)
            stats["folders"] += 1

            directory = config.resolve_to_absolute(physical.repo_id, physical.rel_path)
            if directory is None or not os.path.isdir(directory):
                stats["missing_dir"] += 1
                continue
            nfo_files = sorted(
                path for path in os.listdir(directory)
                if path.lower().endswith(".nfo")
            )
            if not nfo_files:
                stats["no_nfo"] += 1
                continue

            # 优先同名 nfo;否则取第一个能解析出发行日期的
            folder_key = (physical.name or "").casefold()
            candidates = sorted(nfo_files, key=lambda name: name.casefold() != folder_key)
            release_date = None
            used_nfo = None
            for name in candidates:
                parsed = extract_release_date(os.path.join(directory, name))
                if parsed is not None:
                    release_date = parsed
                    used_nfo = name
                    break
            if release_date is None:
                stats["nfo_parse_fail"] += 1
                if len(stats["samples"]) < 10:
                    stats["samples"].append({"id": folder.id, "path": directory, "nfo": nfo_files[:1]})
                continue

            if folder.released_at is not None and not overwrite:
                stats["skipped_existing"] += 1
                continue

            same = folder.released_at is not None and folder.released_at.date() == release_date.date()
            if same:
                stats["skipped_existing"] += 1
                continue

            stats["set"] += 1
            if folder.released_at is not None:
                stats["changed"] += 1
            if len(stats["samples"]) < 10:
                stats["samples"].append({
                    "id": folder.id,
                    "name": physical.name,
                    "path": os.path.join(physical.repo_id, physical.rel_path or ""),
                    "old": folder.released_at.date().isoformat() if folder.released_at else None,
                    "new": release_date.date().isoformat(),
                    "nfo": used_nfo,
                })
            if apply:
                folder.released_at = release_date

        if apply:
            db.commit()
        else:
            db.rollback()
        return stats
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="写入数据库；默认仅预览")
    parser.add_argument("--repo", default=None, help="仅处理该 repo(默认全部)")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的 released_at(默认跳过已有值)")
    args = parser.parse_args()

    if args.apply:
        backup_path = backup_database(config.get_db_path())
        print(f"backup={backup_path}")

    print(f"database={config.get_db_path()}")
    stats = backfill_folder_released_at(
        apply=args.apply, repo=args.repo, overwrite=args.overwrite,
    )
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(
        f"[{mode}] folders={stats['folders']} "
        f"missing_dir={stats['missing_dir']} "
        f"no_nfo={stats['no_nfo']} "
        f"nfo_parse_fail={stats['nfo_parse_fail']} "
        f"set={stats['set']}(changed={stats['changed']}) "
        f"skipped_existing={stats['skipped_existing']}"
    )
    for sample in stats["samples"]:
        print("  sample:", sample)


if __name__ == "__main__":
    main()
