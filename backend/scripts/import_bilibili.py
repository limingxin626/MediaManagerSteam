"""把 /Users/jieli/data/bilibili/<title>/*.mp4 注入为 Message。

每个子目录 = 一条 message:
  - text = 目录名(视频标题)
  - actor_id = None
  - created_at = 目录里所有 mp4 的最早 mtime(下载时间)
  - media = 目录里所有 *.mp4(按文件名排序作为 position 0/1/2…)
  - tag = bilibili(平台 tag,自动 get_or_create)

缩略图:每个 mp4 的同目录如果有同名 `<stem>.cover.{jpg,jpeg,png,webp}`
sidecar(case-insensitive,所以 BBDown 的 `.Cover.jpg` 也命中),backend 会
自动用它作为 thumb,无需脚本干预。这套约定见 media_service._find_video_cover_sidecar。

不做 message 级幂等:重跑会重复建 message(media 由 backend 按 file_hash 自动复用)。
请只跑一次,或先备份 DB。

用法:
    cd backend
    python scripts/import_bilibili.py --dry-run --limit 5
    python scripts/import_bilibili.py --limit 10
    python scripts/import_bilibili.py
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 让 scripts/ 能 import app/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Tag
from app.services.message_service import create_message_with_files

logger = logging.getLogger(__name__)

DEFAULT_ROOT = "/Users/jieli/data/bilibili"
DEFAULT_TAG = "bilibili"


def collect_mp4s(folder: Path) -> list[str]:
    """按文件名排序返回目录下所有 .mp4 的绝对路径。"""
    return sorted(str(p) for p in folder.glob("*.mp4"))


def earliest_mtime(paths: list[str]) -> datetime:
    """取一组文件里最早的 mtime,作为 message.created_at。"""
    return datetime.fromtimestamp(min(os.path.getmtime(p) for p in paths))


def get_or_create_tag(db, name: str) -> Tag:
    t = db.query(Tag).filter(Tag.name == name).first()
    if not t:
        t = Tag(name=name)
        db.add(t)
        db.flush()
        db.commit()
    return t


def import_one(db, folder: Path, tag_id, stats: dict, dry_run: bool) -> None:
    title = folder.name
    mp4s = collect_mp4s(folder)
    if not mp4s:
        print(f"  ⏭  {title}: 无 mp4")
        stats["empty"] += 1
        return

    created_at = earliest_mtime(mp4s)
    print(f"  [{title[:40]}]  mp4={len(mp4s)}  time={created_at}")

    if dry_run:
        for p in mp4s:
            print(f"      {os.path.basename(p)}")
        return

    try:
        msg = create_message_with_files(
            db,
            text=title,
            actor_id=None,
            files=mp4s,
            tag_ids=[tag_id] if tag_id is not None else None,
            created_at=created_at,
            commit=True,
        )
    except Exception as e:
        db.rollback()
        stats["errors"] += 1
        print(f"    ✗ {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return

    stats["imported"] += 1
    stats["files"] += len(mp4s)
    print(f"    ✓ message.id={msg.id}  media={len(msg.message_media)}")


def parse_args():
    ap = argparse.ArgumentParser(description="把 bilibili 下载目录注入为 message")
    ap.add_argument("--root", default=DEFAULT_ROOT,
                    help=f"扫描根目录(默认 {DEFAULT_ROOT})")
    ap.add_argument("--tag", default=DEFAULT_TAG,
                    help=f"每条 message 都加的平台 tag(默认 {DEFAULT_TAG!r})")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印解析预览,不写 DB / 不拷文件")
    ap.add_argument("--limit", type=int, default=None,
                    help="只处理前 N 个子目录(测试用)")
    return ap.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    root = Path(args.root)
    if not root.is_dir():
        print(f"❌ 找不到目录 {root}", file=sys.stderr)
        sys.exit(1)

    folders = sorted(p for p in root.iterdir() if p.is_dir())
    if args.limit:
        folders = folders[: args.limit]

    print(f"root: {root}")
    print(f"folders: {len(folders)}")
    print(f"tag: {args.tag!r}")
    if args.dry_run:
        print("[DRY-RUN] 不写 DB / 不拷文件")
    print()

    stats = {"imported": 0, "errors": 0, "empty": 0, "files": 0}
    db = SessionLocal()
    try:
        tag_id = None if args.dry_run else get_or_create_tag(db, args.tag).id
        for folder in folders:
            import_one(db, folder, tag_id, stats, args.dry_run)
    finally:
        db.close()

    print()
    print("=" * 50)
    for k, v in stats.items():
        print(f"{k:>10}: {v}")


if __name__ == "__main__":
    main()
