"""把 biz_no → category 的映射写回 scratch/bills_by_month/*.json。

用法:
    python apply_categories.py < mapping.json
    # 或
    python apply_categories.py mapping.json

mapping.json 格式: {"<biz_no>": "<category>", ...}

会扫所有月份文件,逐条按 biz_no 匹配并写回。报告:命中 N 条,文件未变 N 条,
mapping 里没匹配上的 biz_no 列表(打错单号会被抛出来)。
"""
import json
import os
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "scratch", "bills_by_month")


def main() -> int:
    src = sys.stdin if len(sys.argv) < 2 else open(sys.argv[1], encoding="utf-8")
    mapping: dict[str, str] = json.load(src)
    if src is not sys.stdin:
        src.close()

    hit_keys: set[str] = set()
    files_touched: dict[str, int] = {}

    for path in sorted(glob.glob(os.path.join(DIR, "*.json"))):
        data = json.load(open(path, encoding="utf-8"))
        changed = 0
        for rec in data:
            cat = mapping.get(rec["biz_no"])
            if cat is None:
                continue
            hit_keys.add(rec["biz_no"])
            if rec.get("category") == cat:
                continue
            rec["category"] = cat
            changed += 1
        if changed:
            json.dump(data, open(path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
            files_touched[os.path.basename(path)] = changed

    print(f"mapping 条目: {len(mapping)}, 命中: {len(hit_keys)}")
    if files_touched:
        for name, n in files_touched.items():
            print(f"  {name}: 写回 {n} 条")
    missing = set(mapping.keys()) - hit_keys
    if missing:
        print(f"\n[警告] {len(missing)} 个 biz_no 未在任何月份文件中匹配上:")
        for k in sorted(missing):
            print(f"  {k}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
