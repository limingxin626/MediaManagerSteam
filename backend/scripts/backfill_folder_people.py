"""Backfill logical ``Folder.people`` (作品演员) from Kodi-style ``.nfo`` files.

每个影片目录放同名的 ``<NAME>.nfo``(如 ``SNIS-752/SNIS-752.nfo``),内含多个
``<actor><name>…</name></actor>``。本脚本以逻辑 Folder 的 PRIMARY 物理目录为准,
读其下 ``*.nfo`` 提取演员名单,get-or-create 到全局 ``Person`` 行并挂到 folder。

只处理 ``kind == "movie"`` 的 folder(与扫描时判片自动解析规则一致)。

默认 dry-run(只打印将发生的变更),加 ``--apply`` 才写库。写库前自动备份 DB。
"""
import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import config  # noqa: E402  (确保 .env 已加载)
from app.models import Folder, FolderLocation, Person, RepositoryFolder, SessionLocal  # noqa: E402
from app.modules.repository.folder_service import parse_folder_nfo_actors  # noqa: E402


def backup_database(db_path: str) -> str:
    import sqlite3
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{db_path}.pre-folder-people-{timestamp}.bak"
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="写库;缺省仅 dry-run 打印")
    parser.add_argument("--repo", default=None, help="只处理指定 repo_id(缺省处理全部)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        rows = (
            db.query(RepositoryFolder, FolderLocation)
            .join(FolderLocation, FolderLocation.repository_folder_id == RepositoryFolder.id)
            .all()
        )
        if args.repo:
            rows = [r for r in rows if r[0].repo_id == args.repo]
        # 每个逻辑 folder 取 PRIMARY(无则 id 最小)物理位置作为 .nfo 来源。
        by_logical: dict[int, RepositoryFolder] = {}
        for physical, location in rows:
            current = by_logical.get(location.folder_id)
            if current is None or (location.role == "PRIMARY" and current.folder_location.role != "PRIMARY"):
                by_logical[location.folder_id] = physical

        cache: dict[str, Person] = {}
        planned: list[tuple[Folder, list[str]]] = []
        for folder_id, physical in sorted(by_logical.items()):
            folder = db.get(Folder, folder_id)
            if folder is None or folder.kind != "movie":
                continue
            actors = parse_folder_nfo_actors(physical)
            if not actors:
                continue
            planned.append((folder, actors))

        if not planned:
            print("no movie folders with parseable .nfo actor lists to update")
            return 0

        existing_names = {p.name for p in db.query(Person).filter(
            Person.name.in_({name for _, names in planned for name in names})
        )}

        print(f"found {len(planned)} movie folder(s) to backfill people:")
        for folder, actors in planned:
            new_names = [name for name in actors if name not in existing_names]
            print(f"  folder #{folder.id} kind={folder.kind} -> {len(actors)} people"
                  + (f"  (+{len(new_names)} new person rows)" if new_names else ""))
            for name in actors:
                print(f"      - {name}{'  [NEW]' if name in new_names else ''}")

        if not args.apply:
            print("\n[DRY-RUN] nothing written; add --apply to persist (auto-backs-up DB).")
            return 0

        db_path = db.get_bind().engine.url.database
        backup = backup_database(db_path)
        print(f"backed up DB -> {backup}")

        updated = 0
        for folder, actors in planned:
            missing = [name for name in actors if name not in cache]
            if missing:
                for person in db.query(Person).filter(Person.name.in_(missing)):
                    cache[person.name] = person
            to_create = [name for name in missing if name not in cache]
            for name in to_create:
                person = Person(name=name, description=None)
                db.add(person)
                db.flush()
                cache[name] = person
            folder.people = [cache[name] for name in actors]
            updated += 1
        db.commit()
        print(f"updated {updated} movie folder(s).")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
