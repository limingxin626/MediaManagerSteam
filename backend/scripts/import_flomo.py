"""
导入 Flomo 笔记到 MediaManagerSteam 数据库。

用法：
    cd backend
    python scripts/import_flomo.py

依赖：
    pip install beautifulsoup4
"""
import sys
import os
import shutil
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from app.models import SessionLocal, Message
from app.config import config
from app.services.media_service import process_file
from app.services.message_service import sync_tags_from_text

# ── 配置 ────────────────────────────────────────────────────────────────────
FLOMO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "flomo@西门吹雪-20260406",
)
HTML_PATH = os.path.join(FLOMO_DIR, "西门吹雪的笔记.html")
# ────────────────────────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("Flomo 导入脚本")
    print(f"HTML 文件: {HTML_PATH}")
    print(f"数据根目录: {config.DATA_ROOT}")
    print("=" * 60)

    if not os.path.exists(HTML_PATH):
        print(f"错误：HTML 文件不存在: {HTML_PATH}")
        sys.exit(1)

    with open(HTML_PATH, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    memos = soup.select("div.memo")
    total = len(memos)
    print(f"共找到 {total} 条笔记\n")

    db = SessionLocal()
    imported = 0
    skipped = 0
    errors = 0

    try:
        for i, memo in enumerate(memos):
            time_tag = memo.find("div", class_="time")
            content_div = memo.find("div", class_="content")

            if not time_tag or not content_div:
                print(f"[{i+1}/{total}] 跳过：缺少 time 或 content")
                skipped += 1
                continue

            time_str = time_tag.get_text(strip=True)
            try:
                memo_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"[{i+1}/{total}] 跳过：无法解析时间 '{time_str}'")
                skipped += 1
                continue

            plain_text = content_div.get_text(separator="\n").strip()

            # 去重检查
            existing = db.query(Message).filter(
                Message.text == plain_text,
                Message.created_at == memo_dt,
            ).first()
            if existing:
                skipped += 1
                continue

            # 收集图片路径
            files_div = memo.find("div", class_="files")
            image_srcs = []
            if files_div:
                for img in files_div.find_all("img"):
                    src = img.get("src", "")
                    if src:
                        image_srcs.append(src)

            try:
                # 创建 Message（时间戳使用 flomo 原始时间）
                db_message = Message(
                    text=plain_text,
                    actor_id=None,
                    created_at=memo_dt,
                    updated_at=memo_dt,
                )
                db.add(db_message)
                db.flush()

                # 同步 #hashtag → Tag
                sync_tags_from_text(db, db_message, plain_text)

                # 处理图片附件
                upload_dir = config.get_upload_dir()
                os.makedirs(upload_dir, exist_ok=True)

                for position, src in enumerate(image_srcs):
                    # src 格式: file/2026-03-30/1847363/xxx.jpg
                    rel_path = src.replace("/", os.sep)
                    abs_src = os.path.normpath(os.path.join(FLOMO_DIR, rel_path))

                    if not os.path.exists(abs_src):
                        print(f"  警告：图片不存在 {abs_src}")
                        continue

                    dest = os.path.join(upload_dir, os.path.basename(abs_src))
                    if not os.path.exists(dest):
                        shutil.copy2(abs_src, dest)

                    result = process_file(db, dest, db_message.id, position)
                    if result is None:
                        print(f"  警告：process_file 返回 None，跳过 {dest}")

                db.commit()
                imported += 1

                if (imported + skipped) % 20 == 0 or i == total - 1:
                    print(f"进度 [{i+1}/{total}] 已导入: {imported}, 已跳过: {skipped}, 错误: {errors}")

            except Exception as e:
                db.rollback()
                errors += 1
                print(f"[{i+1}/{total}] 错误（{time_str}）: {e}")
                traceback.print_exc()

    finally:
        db.close()

    print("\n" + "=" * 60)
    print(f"导入完成：Imported={imported}, Skipped={skipped}, Errors={errors}, Total={total}")
    print("=" * 60)


if __name__ == "__main__":
    main()
