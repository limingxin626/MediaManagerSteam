"""交易分类与导入。

分类策略(命中优先级从高到低):
  1. 关键词规则表 txn_category_rule:keyword 命中「交易对方 + 商品」文本 → category
  2. 字段信号兜底:支付宝来源地=淘宝 → 购物;微信交易类型(转账/红包/二维码)粗分
  3. 仍未命中 → 「未分类」

导入按 (source, biz_no) 源内去重,重复导入幂等。
service 内只 db.flush(),commit 交给调用方(CLI / router)。
"""
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Transaction, TxnCategoryRule

UNCLASSIFIED = "未分类"

# 默认关键词规则:(keyword, category, priority)。基于真实账单里出现的商户/商品。
DEFAULT_RULES: list[tuple[str, str, int]] = [
    # 数字订阅 / 软件
    ("CodePlanPlus", "数字订阅", 90),
    ("稀宇科技", "数字订阅", 90),
    ("会员", "数字订阅", 50),
    ("Steam", "数字订阅", 80),
    ("Valve", "数字订阅", 80),
    ("App Store", "数字订阅", 80),
    ("apple.com", "数字订阅", 80),
    ("腾讯视频", "数字订阅", 80),
    ("爱奇艺", "数字订阅", 80),
    ("网易云", "数字订阅", 70),
    # 餐饮
    ("美团", "餐饮", 70),
    ("饿了么", "餐饮", 70),
    ("肯德基", "餐饮", 80),
    ("麦当劳", "餐饮", 80),
    ("星巴克", "餐饮", 80),
    ("瑞幸", "餐饮", 80),
    ("蜜雪", "餐饮", 80),
    ("餐厅", "餐饮", 50),
    ("餐饮", "餐饮", 50),
    ("食品", "餐饮", 40),
    ("熟食", "餐饮", 50),
    ("凉菜", "餐饮", 50),
    ("蔬菜水果", "餐饮", 50),
    ("水果", "餐饮", 40),
    ("超市", "餐饮", 40),
    ("便利店", "餐饮", 40),
    # 交通
    ("滴滴", "交通", 80),
    ("出行", "交通", 60),
    ("地铁", "交通", 80),
    ("公交", "交通", 80),
    ("高德", "交通", 60),
    ("12306", "交通", 90),
    ("铁路", "交通", 80),
    ("加油", "交通", 70),
    ("停车", "交通", 60),
    # 购物
    ("优衣库", "购物", 80),
    ("京东", "购物", 70),
    ("天猫", "购物", 70),
    ("淘宝", "购物", 60),
    ("拼多多", "购物", 70),
    ("服饰", "购物", 50),
    ("旗舰店", "购物", 40),
    # 居家 / 生活缴费
    ("电费", "生活缴费", 80),
    ("水费", "生活缴费", 80),
    ("燃气", "生活缴费", 80),
    ("话费", "生活缴费", 80),
    ("中国移动", "生活缴费", 70),
    ("中国联通", "生活缴费", 70),
    ("中国电信", "生活缴费", 70),
    ("物业", "生活缴费", 70),
    # 转账 / 红包(往来款)
    ("红包", "转账红包", 30),
    ("转账", "转账红包", 20),
]


def _seed_default_rules(db: Session) -> int:
    """首次导入时写入默认规则(已存在的 keyword 跳过)。返回新增条数。"""
    existing = {k for (k,) in db.query(TxnCategoryRule.keyword).all()}
    added = 0
    for keyword, category, priority in DEFAULT_RULES:
        if keyword in existing:
            continue
        db.add(TxnCategoryRule(keyword=keyword, category=category, priority=priority))
        added += 1
    if added:
        db.flush()
    return added


def _load_rules(db: Session) -> List[TxnCategoryRule]:
    """按 priority 降序加载规则(高优先级先匹配)。"""
    return db.query(TxnCategoryRule).order_by(TxnCategoryRule.priority.desc(), TxnCategoryRule.id.asc()).all()


def classify(record: dict, rules: List[TxnCategoryRule]) -> str:
    """对单条记录分类:关键词规则 → 字段信号兜底 → 未分类。"""
    text = f"{record.get('counterparty') or ''} {record.get('product') or ''}"
    for rule in rules:
        if rule.keyword in text:
            return rule.category

    # 字段信号兜底
    origin = record.get("raw_origin") or ""
    raw_type = record.get("raw_type") or ""
    if "淘宝" in origin or "阿里巴巴" in origin:
        return "购物"
    if "转账" in raw_type or "红包" in raw_type:
        return "转账红包"
    if "二维码" in raw_type:
        return "餐饮"  # 扫码付款多为线下小额消费,粗归餐饮,用户可后续改规则

    return UNCLASSIFIED


def import_records(db: Session, records: List[dict]) -> dict:
    """批量导入:源内 (source, biz_no) 去重,新记录分类后入库。

    返回 {inserted, skipped, by_category: {cat: {count, amount}}}。
    """
    if not records:
        return {"inserted": 0, "skipped": 0, "by_category": {}}

    _seed_default_rules(db)
    rules = _load_rules(db)

    # 批量取已存在的 (source, biz_no),避免逐条查询
    sources = {r["source"] for r in records}
    existing = set()
    for src in sources:
        for (biz_no,) in db.query(Transaction.biz_no).filter(Transaction.source == src).all():
            existing.add((src, biz_no))

    inserted = 0
    skipped = 0
    by_category: dict[str, dict] = {}
    seen_in_batch = set()

    for rec in records:
        key = (rec["source"], rec["biz_no"])
        if key in existing or key in seen_in_batch:
            skipped += 1
            continue
        seen_in_batch.add(key)

        category = classify(rec, rules)
        db.add(Transaction(
            source=rec["source"],
            biz_no=rec["biz_no"],
            txn_time=rec["txn_time"],
            direction=rec["direction"],
            amount=rec["amount"],
            counterparty=rec.get("counterparty"),
            product=rec.get("product"),
            category=category,
            raw_type=rec.get("raw_type"),
            raw_origin=rec.get("raw_origin"),
            status=rec.get("status"),
            excluded=rec.get("excluded", 0),
        ))
        inserted += 1

        # 仅统计计入的支出
        if rec.get("excluded", 0) == 0 and rec["direction"] == "expense":
            slot = by_category.setdefault(category, {"count": 0, "amount": 0.0})
            slot["count"] += 1
            slot["amount"] += rec["amount"]

    db.flush()
    return {"inserted": inserted, "skipped": skipped, "by_category": by_category}


def _summary_query(db: Session, direction: str = "expense"):
    """基础聚合:默认只统计未排除的支出。"""
    return (
        db.query(Transaction)
        .filter(Transaction.excluded == 0, Transaction.direction == direction)
    )


def monthly_summary(db: Session, year: int, month: int, direction: str = "expense") -> dict:
    """某月按分类的支出汇总。"""
    from datetime import datetime
    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    rows = (
        _summary_query(db, direction)
        .filter(Transaction.txn_time >= start, Transaction.txn_time < end)
        .with_entities(Transaction.category, func.count(Transaction.id), func.sum(Transaction.amount))
        .group_by(Transaction.category)
        .all()
    )
    total = sum(float(amt or 0) for _, _, amt in rows)
    return {
        "year": year, "month": month, "total": total,
        "by_category": {cat or UNCLASSIFIED: {"count": cnt, "amount": float(amt or 0)} for cat, cnt, amt in rows},
    }


def category_summary(db: Session, direction: str = "expense") -> dict:
    """全量按分类的支出汇总。"""
    rows = (
        _summary_query(db, direction)
        .with_entities(Transaction.category, func.count(Transaction.id), func.sum(Transaction.amount))
        .group_by(Transaction.category)
        .all()
    )
    total = sum(float(amt or 0) for _, _, amt in rows)
    return {
        "total": total,
        "by_category": {cat or UNCLASSIFIED: {"count": cnt, "amount": float(amt or 0)} for cat, cnt, amt in rows},
    }
