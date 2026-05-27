"""
脚本：清空 text 只保留 tags

用法：python find_text_equals_tag.py --update

将 text 完全等于 tag 组合的 message 的 text 清空（设为空字符串），
同时保留 message_tag 关联表中的 tags。
"""
import re
import sqlite3
import argparse

DB_PATH = "E:/AskTao/data/db.sqlite3"

# 与后端 sync_tags_from_text 相同的正则
HASHTAG_PATTERN = re.compile(r'#([\w\u4e00-\u9fff\u3400-\u4dbf/\-]+)')


def extract_tags_from_text(text):
    """从 text 中提取 #tag，返回 tag name 列表"""
    if not text:
        return []
    return HASHTAG_PATTERN.findall(text)


def is_pure_tag_combination(text, all_tags):
    """检查 text 是否完全等于 tag 组合（没有其他内容）"""
    if not text:
        return False, []

    tags = HASHTAG_PATTERN.findall(text)
    if not tags:
        return False, []

    if not all(t in all_tags for t in tags):
        return False, []

    cleaned = text
    for tag in tags:
        cleaned = cleaned.replace(f"#{tag}", "")

    cleaned = cleaned.strip()

    if cleaned == "":
        return True, tags
    return False, []


def find_messages_to_update():
    """查找需要更新的 message"""
    conn = sqlite3.connect(DB_PATH)
    conn.isolation_level = None  # autocommit
    cursor = conn.cursor()

    # 获取所有 tag 名称
    cursor.execute("SELECT name FROM tag")
    tag_names = {row[0] for row in cursor.fetchall()}
    print(f"共有 {len(tag_names)} 个 Tag")

    # 获取所有 message（text 不为空）
    cursor.execute("SELECT id, text FROM message WHERE text IS NOT NULL AND text != ''")
    messages = cursor.fetchall()

    to_update = []

    for msg_id, text in messages:
        is_pure, matched_tags = is_pure_tag_combination(text, tag_names)
        if is_pure:
            to_update.append((msg_id, text, matched_tags))

    conn.close()
    return to_update


def update_messages(to_update):
    """清空 text"""
    conn = sqlite3.connect(DB_PATH)
    conn.isolation_level = None
    cursor = conn.cursor()

    cursor.execute("BEGIN TRANSACTION")

    updated = 0
    for msg_id, text, matched_tags in to_update:
        cursor.execute("UPDATE message SET text = '' WHERE id = ?", (msg_id,))
        updated += 1

        if updated % 100 == 0:
            print(f"已更新 {updated}/{len(to_update)} ...")

    cursor.execute("COMMIT")
    conn.close()

    return updated


def main():
    parser = argparse.ArgumentParser(description="清空 text 只保留 tags")
    parser.add_argument("--update", action="store_true", help="执行更新（默认只预览）")
    args = parser.parse_args()

    print("=" * 60)
    print("查找 text 完全等于 tag 组合的 Message")
    print("=" * 60)

    to_update = find_messages_to_update()
    print(f"\n找到 {len(to_update)} 条需要清空 text 的 Message:\n")

    # 预览前 10 条
    for msg_id, text, matched_tags in to_update[:10]:
        print(f"  ID: {msg_id}, text: {text[:50]}..." if len(text) > 50 else f"  ID: {msg_id}, text: {text}")
        print(f"    matched_tags: {matched_tags}")

    if len(to_update) > 10:
        print(f"  ... 还有 {len(to_update) - 10} 条未显示")

    if args.update:
        print("\n执行更新...")
        updated = update_messages(to_update)
        print(f"\n已更新 {updated} 条 message 的 text 为空字符串")
    else:
        print("\n加上 --update 参数执行更新")


if __name__ == "__main__":
    main()