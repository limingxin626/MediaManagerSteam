"""账单导入 CLI。

用法(在 backend/ 下用项目 venv 运行):
    python import_bills.py                 # 扫 ../slip/ 下所有 .csv / .xlsx
    python import_bills.py --dir PATH      # 指定账单目录
    python import_bills.py --dry-run       # 只解析+分类打印统计,不写库

支付宝导出 CSV、微信导出 xlsx 放进 slip/ 文件夹后跑本脚本即可导入。
重复导入幂等(按 source + 交易号去重)。
"""
import argparse
import glob
import os
import sys

# 允许直接 `python import_bills.py` 运行(确保能 import app.*)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, Transaction  # noqa: E402
from app.services import bill_parser  # noqa: E402
from app.services import transaction_service as txn_svc  # noqa: E402

DEFAULT_SLIP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "slip")


def _discover(folder: str) -> list[str]:
    """收集目录下的账单文件(.csv / .xlsx),忽略临时文件。"""
    files = []
    for pattern in ("*.csv", "*.xlsx"):
        for p in glob.glob(os.path.join(folder, pattern)):
            name = os.path.basename(p)
            if name.startswith("~$") or name.startswith("."):
                continue
            files.append(p)
    return sorted(files)


def _fmt_categories(by_category: dict) -> str:
    if not by_category:
        return "    (无计入统计的支出)"
    lines = []
    for cat, info in sorted(by_category.items(), key=lambda kv: -kv[1]["amount"]):
        lines.append(f"    {cat:8s}  {info['count']:4d} 笔  {info['amount']:>12.2f} 元")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="导入支付宝/微信账单到本地数据库")
    parser.add_argument("--dir", default=DEFAULT_SLIP_DIR, help="账单目录(默认 ../slip)")
    parser.add_argument("--dry-run", action="store_true", help="只解析打印,不写库")
    args = parser.parse_args()

    folder = os.path.abspath(args.dir)
    if not os.path.isdir(folder):
        print(f"[错误] 目录不存在: {folder}")
        return 1

    files = _discover(folder)
    if not files:
        print(f"[提示] {folder} 下没有找到 .csv / .xlsx 账单文件")
        return 0

    print(f"扫描目录: {folder}")
    print(f"发现 {len(files)} 个账单文件\n")

    # 解析全部文件 → 汇总记录
    all_records: list[dict] = []
    for path in files:
        name = os.path.basename(path)
        try:
            records = bill_parser.parse_file(path)
        except Exception as e:  # noqa: BLE001
            print(f"  [跳过] {name}: 解析失败 — {e}")
            continue
        src = records[0]["source"] if records else "?"
        excluded = sum(1 for r in records if r.get("excluded"))
        print(f"  [{src:6s}] {name}: 解析 {len(records)} 条(其中 {excluded} 条退款/关闭/0元已标记不计统计)")
        all_records.extend(records)

    if not all_records:
        print("\n没有可导入的记录。")
        return 0

    db = SessionLocal()
    try:
        if args.dry_run:
            # 仅分类预览,不写库:用内存规则跑一遍分类统计
            txn_svc._seed_default_rules(db)  # 仅在内存 session,稍后回滚
            rules = txn_svc._load_rules(db)
            by_category: dict[str, dict] = {}
            for rec in all_records:
                if rec.get("excluded", 0) == 0 and rec["direction"] == "expense":
                    cat = txn_svc.classify(rec, rules)
                    slot = by_category.setdefault(cat, {"count": 0, "amount": 0.0})
                    slot["count"] += 1
                    slot["amount"] += rec["amount"]
            db.rollback()
            total = sum(v["amount"] for v in by_category.values())
            print(f"\n=== DRY-RUN(未写库)===")
            print(f"将导入 {len(all_records)} 条记录")
            print(f"计入统计的支出合计: {total:.2f} 元,按分类:")
            print(_fmt_categories(by_category))
            return 0

        result = txn_svc.import_records(db, all_records)
        db.commit()

        total = sum(v["amount"] for v in result["by_category"].values())
        print(f"\n=== 导入完成 ===")
        print(f"新增 {result['inserted']} 条,跳过(已存在){result['skipped']} 条")
        print(f"本次新增中计入统计的支出合计: {total:.2f} 元,按分类:")
        print(_fmt_categories(result["by_category"]))

        # 库内总览
        grand = txn_svc.category_summary(db)
        print(f"\n=== 数据库总览(全部已计入支出)===")
        print(f"累计支出合计: {grand['total']:.2f} 元")
        print(_fmt_categories(grand["by_category"]))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
