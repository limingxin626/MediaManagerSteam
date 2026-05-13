"""一次性数据迁移：把旧 todo 表的数据复制到新 issue 表。

- pending / doing → doing
- done → done

运行：
    cd backend && python scripts/migrate_todo_to_issue.py
幂等：通过 title 去重，已存在的 issue 不会重复插入。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Todo, Issue  # noqa: E402


STATUS_MAP = {
    "pending": "doing",
    "doing": "doing",
    "done": "done",
}


def main():
    db = SessionLocal()
    try:
        todos = db.query(Todo).all()
        if not todos:
            print("无 todo 数据，跳过")
            return

        existing_titles = {i.title for i in db.query(Issue).all()}

        # 按目标 status 分桶，position 重新编号
        buckets: dict[str, list[Todo]] = {"doing": [], "done": []}
        for t in todos:
            target = STATUS_MAP.get(t.status, "doing")
            buckets[target].append(t)

        # 保持原 position 顺序
        for target, items in buckets.items():
            items.sort(key=lambda x: (x.status, x.position))

        # 起始 position：跟在已有 issue 之后
        start_pos: dict[str, int] = {}
        for target in buckets:
            existing = db.query(Issue).filter(Issue.status == target).count()
            start_pos[target] = existing

        inserted = 0
        for target, items in buckets.items():
            pos = start_pos[target]
            for t in items:
                if t.title in existing_titles:
                    print(f"跳过(title 已存在): {t.title}")
                    continue
                issue = Issue(
                    title=t.title,
                    description=None,
                    status=target,
                    position=pos,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    completed_at=t.completed_at if target == "done" else None,
                )
                db.add(issue)
                existing_titles.add(t.title)
                pos += 1
                inserted += 1

        db.commit()
        print(f"迁移完成：插入 {inserted} 条 issue")
    finally:
        db.close()


if __name__ == "__main__":
    main()
