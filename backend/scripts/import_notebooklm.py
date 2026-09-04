"""
导入 Obsidian 中整理好的 NotebookLM 分析笔记到 MediaManagerSteam 数据库。

- 每个 .md 文件 → 一条 Message（正文 markdown 存入 text，时间戳为导出日 2026-08-24）
- 每条消息挂到一个新建的 Collection「NotebookLM」
- frontmatter 里的 tags 映射为 Tag（不存在则新建）并建立 message_tag 关联
- 幂等：同一正文已存在则跳过（可安全重跑）

用法：
    cd backend
    .venv/bin/python scripts/import_notebooklm.py
"""
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Message, Tag, Collection

# 6 篇 AI 分析笔记所在目录（Obsidian 仓库）
NOTES_DIR = "/Users/jieli/Documents/笑忘书/笑忘书/notebooklm/笔记"
COLLECTION_NAME = "NotebookLM"
CREATED_AT = datetime(2026, 8, 24, 16, 52, 0)  # 导出时间；每条错开 1s 保证 feed 排序稳定


def parse_frontmatter(text: str):
    """解析文件头 `---` 之间的 YAML（简单解析 title / created / tags）。"""
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    fm = {"title": None, "created": None, "tags": []}
    if not m:
        return fm, text
    block = m.group(1)
    for line in block.splitlines():
        line = line.rstrip()
        if line.startswith("title:"):
            fm["title"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("created:"):
            fm["created"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("  - "):
            fm["tags"].append(line[4:].strip())
    body = text[m.end():].lstrip("\n")
    return fm, body


def wikilink_to_plain(text: str) -> str:
    """把 Obsidian 双链 `[[目标|别名]]` / `[[目标]]` 转成可读纯文本。"""
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    return text


def main():
    if not os.path.isdir(NOTES_DIR):
        print(f"错误：笔记目录不存在: {NOTES_DIR}")
        sys.exit(1)

    files = sorted(
        f for f in os.listdir(NOTES_DIR)
        if f.endswith(".md") and not f.startswith(".")
    )
    print("=" * 60)
    print("NotebookLM 笔记导入")
    print(f"目录: {NOTES_DIR}")
    print(f"数据根: {__import__('app.config', fromlist=['config']).config.DATA_ROOT}")
    print(f"待导入 {len(files)} 篇")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 1) 确保 Collection 存在
        collection = db.query(Collection).filter(Collection.name == COLLECTION_NAME).first()
        if not collection:
            collection = Collection(name=COLLECTION_NAME,
                                    description="2026-08-24 从 NotebookLM 导出的 AI 分析笔记")
            db.add(collection)
            db.flush()
            print(f"创建 Collection: {COLLECTION_NAME} (id={collection.id})")
        else:
            print(f"复用 Collection: {COLLECTION_NAME} (id={collection.id})")

        imported = skipped = errors = 0
        for i, name in enumerate(files):
            with open(os.path.join(NOTES_DIR, name), encoding="utf-8") as f:
                raw = f.read()
            fm, body = parse_frontmatter(raw)
            text = wikilink_to_plain(body).strip()

            if not text:
                print(f"[{i+1}] 跳过（正文为空）: {name}")
                skipped += 1
                continue

            # 幂等去重：同正文同时间戳视为已导入
            existing = db.query(Message).filter(
                Message.text == text, Message.created_at == CREATED_AT
            ).first()
            if existing:
                print(f"[{i+1}] 跳过（已存在, id={existing.id}）: {name}")
                skipped += 1
                continue

            try:
                msg = Message(
                    text=text,
                    collection_id=collection.id,
                    created_at=datetime(CREATED_AT.year, CREATED_AT.month, CREATED_AT.day,
                                        CREATED_AT.hour, CREATED_AT.minute, CREATED_AT.second + i),
                    updated_at=datetime(CREATED_AT.year, CREATED_AT.month, CREATED_AT.day,
                                        CREATED_AT.hour, CREATED_AT.minute, CREATED_AT.second + i),
                )
                db.add(msg)
                db.flush()

                # 2) frontmatter tags → Tag 行 + message_tag 关联
                tags = []
                for tname in dict.fromkeys(fm["tags"]):  # 去重保序
                    if not tname:
                        continue
                    tag = db.query(Tag).filter(Tag.name == tname).first()
                    if not tag:
                        tag = Tag(name=tname)
                        db.add(tag)
                        db.flush()
                    tags.append(tag)
                msg.tags = tags

                db.commit()
                imported += 1
                print(f"[{i+1}] 已导入: {name} (msg_id={msg.id}, tags={[t.name for t in tags]})")
            except Exception as e:
                db.rollback()
                errors += 1
                print(f"[{i+1}] 错误: {name} -> {e}")

        print("\n" + "=" * 60)
        print(f"完成：Imported={imported}, Skipped={skipped}, Errors={errors}")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()
