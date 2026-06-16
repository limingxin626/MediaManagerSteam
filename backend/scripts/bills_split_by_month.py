"""把 slip/ 下所有账单解析后按月切分,输出到 scratch/bills_by_month/YYYY-MM.json。

每条记录的字段就是 bill_parser 输出的那些(time 序列化为 ISO 字符串),
另加一个空的 category 字段供后续打标签填充。
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import bill_parser  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLIP_DIR = os.path.normpath(os.path.join(ROOT, "..", "slip"))
OUT_DIR = os.path.join(ROOT, "scratch", "bills_by_month")


def _serialize(rec: dict) -> dict:
    out = dict(rec)
    out["txn_time"] = rec["txn_time"].isoformat()
    out["category"] = ""  # 待打
    return out


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)

    all_records: list[dict] = []
    for name in sorted(os.listdir(SLIP_DIR)):
        path = os.path.join(SLIP_DIR, name)
        if not os.path.isfile(path):
            continue
        if not (name.endswith(".csv") or name.endswith(".xlsx")):
            continue
        recs = bill_parser.parse_file(path)
        all_records.extend(recs)
        print(f"  {name}: {len(recs)} 条")

    # 按月分桶
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in all_records:
        key = r["txn_time"].strftime("%Y-%m")
        buckets[key].append(_serialize(r))

    # 每月内按时间升序,便于人工浏览
    for key in buckets:
        buckets[key].sort(key=lambda r: r["txn_time"])

    for key in sorted(buckets):
        out_path = os.path.join(OUT_DIR, f"{key}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(buckets[key], f, ensure_ascii=False, indent=2)
        print(f"  写出 {out_path}: {len(buckets[key])} 条")

    total = sum(len(v) for v in buckets.values())
    print(f"\n合计 {total} 条,分到 {len(buckets)} 个月份文件,输出目录: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
