"""精简打印一个月的账单,只留打标需要的列。

用法: python bills_print_month.py 2025-07

输出每行: biz_no | date | dir | amount | counterparty | product | raw_type | raw_origin | excluded | current_category
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python bills_print_month.py YYYY-MM")
        return 1
    ym = sys.argv[1]
    path = os.path.join(ROOT, "scratch", "bills_by_month", f"{ym}.json")
    data = json.load(open(path, encoding="utf-8"))
    for r in data:
        print(" | ".join([
            r["biz_no"],
            r["txn_time"][:16],
            r["direction"][:3],
            f'{r["amount"]:.2f}',
            (r.get("counterparty") or "")[:30],
            (r.get("product") or "")[:40],
            (r.get("raw_type") or "")[:12],
            (r.get("raw_origin") or "")[:14],
            "X" if r.get("excluded") else "",
            r.get("category") or "",
        ]))
    print(f"\n# 共 {len(data)} 条, 未标 {sum(1 for r in data if not r.get('category'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
