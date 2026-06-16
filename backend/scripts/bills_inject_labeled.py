"""清空 transaction 表,从 scratch/bills_by_month/*.json 注入(category 已人工打好)。

危险操作:--apply 才真正执行,默认 --dry-run 只打印将执行的动作。

用法:
    python bills_inject_labeled.py             # dry-run
    python bills_inject_labeled.py --apply     # 真删真写
"""
import argparse
import glob
import json
import os
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Transaction, TxnCategoryRule  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "scratch", "bills_by_month")


def _load() -> list[dict]:
    out = []
    for p in sorted(glob.glob(os.path.join(DIR, "*.json"))):
        data = json.load(open(p, encoding="utf-8"))
        for r in data:
            r["txn_time"] = datetime.fromisoformat(r["txn_time"])
            out.append(r)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="真正清库 + 注入(默认 dry-run)")
    args = parser.parse_args()

    records = _load()
    unlabeled = [r for r in records if not r.get("category")]
    if unlabeled:
        print(f"[错误] 还有 {len(unlabeled)} 条未打标签,中止")
        for r in unlabeled[:5]:
            print(f"  {r['biz_no']} {r['counterparty']} {r['product']}")
        return 1

    by_cat = Counter(r["category"] for r in records)
    print(f"待注入 {len(records)} 条;分布:")
    for cat, n in by_cat.most_common():
        print(f"  {cat:8s}  {n:5d}")

    if not args.apply:
        print()
        print("DRY-RUN: 未真正动数据库。加 --apply 才执行。")
        return 0

    db = SessionLocal()
    try:
        old_n = db.query(Transaction).count()
        old_rules = db.query(TxnCategoryRule).count()
        print(f"\n清空前:transaction {old_n} 条,txn_category_rule {old_rules} 条")
        db.query(Transaction).delete()
        # 规则表也清掉:已经全人工标好,旧规则不再需要,后续也不会自动分类
        db.query(TxnCategoryRule).delete()

        for r in records:
            db.add(Transaction(
                source=r["source"],
                biz_no=r["biz_no"],
                txn_time=r["txn_time"],
                direction=r["direction"],
                amount=r["amount"],
                counterparty=r.get("counterparty"),
                product=r.get("product"),
                category=r["category"],
                raw_type=r.get("raw_type"),
                raw_origin=r.get("raw_origin"),
                status=r.get("status"),
                excluded=r.get("excluded", 0),
            ))
        db.commit()
        new_n = db.query(Transaction).count()
        print(f"清空 + 注入完成:transaction 现在 {new_n} 条")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
