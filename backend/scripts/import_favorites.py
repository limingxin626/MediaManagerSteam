"""
导入 xsijishe.com 收藏抓取结果到 MediaManagerSteam 数据库。

输入: scrape_pw.py 产生的目录
    <scrape_dir>/
      favorites.json
      threads/<tid>/
        thread.json
        attachments/<post_id>/<filename>

输出: 写入 backend/db.sqlite3
    - 1 message / thread(post 文本合并,正文末尾追加 `imported:<tid>` 一行)
    - N media(thread 内所有附件,按出现顺序)
    - 1 tag / message: 司机社(平台)
    - actor_id 留空(导入内容不关联作者)

幂等: 重跑时通过查 `message.text LIKE '%imported:<tid>%'` 跳过。

用法:
    cd backend
    python scripts/import_favorites.py
    python scripts/import_favorites.py --scrape-dir /path/to/scrape
    python scripts/import_favorites.py --dry-run
    python scripts/import_favorites.py --platform-tag 司机社
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 让 scripts/ 能 import app/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Message, SessionLocal, Tag
from app.services.message_service import create_message_with_files

DEFAULT_SCRAPE_DIR = "/private/tmp/_pw_full"
DEFAULT_PLATFORM_TAG = "司机社"
DEFAULT_DEDUP_PREFIX = "imported:"


# ── helpers ────────────────────────────────────────────────────────────────

def parse_args():
    import argparse
    ap = argparse.ArgumentParser(description="把 scrape_pw.py 抓取的收藏导入 DB")
    ap.add_argument("--scrape-dir", default=DEFAULT_SCRAPE_DIR,
                    help=f"scrape_pw.py 输出目录(默认 {DEFAULT_SCRAPE_DIR})")
    ap.add_argument("--platform-tag", default=DEFAULT_PLATFORM_TAG,
                    help=f"每条 message 都加的平台 tag(默认 {DEFAULT_PLATFORM_TAG!r})")
    ap.add_argument("--dedup-prefix", default=DEFAULT_DEDUP_PREFIX,
                    help=f"幂等标记 tag 前缀(默认 {DEFAULT_DEDUP_PREFIX!r})")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印解析预览,不写 DB")
    return ap.parse_args()


def get_or_create_tag(db, name: str) -> Tag:
    t = db.query(Tag).filter(Tag.name == name).first()
    if not t:
        t = Tag(name=name)
        db.add(t)
        db.flush()
    return t


def has_dedup_marker(db, tid: str) -> bool:
    """查 message.text 是否已含 `imported:<tid>`(上一轮导入了就不再重复)。"""
    marker = f"imported:{tid}"
    return db.query(Message.id).filter(Message.text.like(f"%{marker}%")).first() is not None


def parse_created_at(raw: Optional[str]) -> datetime:
    if not raw:
        return datetime.now()
    # scrape_pw.js 出的格式: "2026-6-10 13:01:14"(月份/日不补零)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    print(f"    ⚠️  无法解析时间 {raw!r}, 用当前时间", file=sys.stderr)
    return datetime.now()


def merge_posts_text(posts: list[dict], title: str, dedup_marker: str = "") -> str:
    """把所有有内容的帖子合并成一段,每段以 `## 楼层 · 用户` 起头,标题置顶。

    若提供了 dedup_marker(如 "imported:678812"),作为最后一行追加。
    """
    sections = [f"# {title}"]
    for p in posts:
        content = (p.get("content") or "").strip()
        if not content:
            continue
        floor = p.get("floor") or "?"
        user = p.get("username") or "?"
        time = p.get("time") or ""
        meta = f"  ".join(x for x in [floor, user, time] if x)
        sections.append(f"## {meta}\n{content}")
    if dedup_marker:
        sections.append(dedup_marker)
    return "\n\n".join(sections)


def collect_file_paths(posts: list[dict]) -> list[str]:
    """按 post 出现顺序收集已下载到本地的附件绝对路径(跳过 download_ok=False)。"""
    paths = []
    for p in posts:
        for a in p.get("attachments") or []:
            if not a.get("download_ok"):
                continue
            lp = a.get("local_path")
            if lp and os.path.exists(lp):
                paths.append(lp)
    return paths


# ── 单条导入 ────────────────────────────────────────────────────────────────

def import_one(db, thread_path: Path, args, stats: dict) -> None:
    thread_json = thread_path / "thread.json"
    if not thread_json.exists():
        print(f"  ✗ {thread_path.name}: 缺 thread.json", file=sys.stderr)
        stats["errors"] += 1
        return

    with open(thread_json, encoding="utf-8") as f:
        data = json.load(f)

    tid = thread_path.name
    posts = data.get("posts") or []
    if not posts:
        print(f"  ✗ {tid}: posts 为空", file=sys.stderr)
        stats["errors"] += 1
        return

    first = posts[0]
    title = data.get("title") or "(无标题)"
    created_at = parse_created_at(first.get("time"))
    files = collect_file_paths(posts)
    dedup_marker = f"{args.dedup_prefix}{tid}"
    text = merge_posts_text(posts, title, dedup_marker=dedup_marker)

    preview = text.replace("\n", " ")[:80]
    last_line = text.rstrip().split("\n\n")[-1]
    print(f"  [{tid}] {title[:30]}")
    print(f"    time={created_at}  files={len(files)}  text={preview!r}")
    print(f"    last line = {last_line!r}")

    if args.dry_run:
        return

    # 幂等检查:已导入的 thread 会在 text 末尾有 imported:<tid> 一行
    if has_dedup_marker(db, tid):
        print(f"    ⏭  跳过(已存在 {dedup_marker} 标记)")
        stats["skipped"] += 1
        return

    try:
        tag_platform = get_or_create_tag(db, args.platform_tag)
        tag_ids = [tag_platform.id]

        msg = create_message_with_files(
            db,
            text=text,
            actor_id=None,  # 导入的内容不关联作者
            files=files,
            tag_ids=tag_ids,
            created_at=created_at,
            commit=True,
        )
        stats["imported"] += 1
        stats["attachments"] += len(files)
        n_media = len(msg.message_media or [])
        print(f"    ✓ message.id={msg.id}  media={n_media}")
    except Exception as e:
        db.rollback()
        stats["errors"] += 1
        print(f"    ✗ {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)


# ── 入口 ────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    scrape_dir = Path(args.scrape_dir)
    threads_dir = scrape_dir / "threads"
    if not threads_dir.is_dir():
        print(f"❌ 找不到 {threads_dir}", file=sys.stderr)
        sys.exit(1)

    thread_dirs = sorted(p for p in threads_dir.iterdir() if p.is_dir())
    print(f"scrape 目录: {scrape_dir}")
    print(f"待处理 thread: {len(thread_dirs)}")
    print(f"platform tag: {args.platform_tag!r}  dedup prefix: {args.dedup_prefix!r}")
    if args.dry_run:
        print("[DRY-RUN] 不写 DB")
    print()

    stats = {"imported": 0, "skipped": 0, "errors": 0, "attachments": 0}
    db = SessionLocal()
    try:
        for td in thread_dirs:
            import_one(db, td, args, stats)
    finally:
        db.close()

    print()
    print("=" * 50)
    print(f"imported:    {stats['imported']}")
    print(f"skipped:     {stats['skipped']}")
    print(f"errors:      {stats['errors']}")
    print(f"attachments: {stats['attachments']}")


if __name__ == "__main__":
    main()
