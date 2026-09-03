"""账单解析器:支付宝 CSV(GBK)与微信 xlsx → 标准化记录 dict 列表。

纯函数,不依赖数据库,便于单测。每条记录统一为:
    {source, biz_no, txn_time, direction, amount, counterparty,
     product, raw_type, raw_origin, status, excluded}

为抵御账单改版,列定位一律按「列名」而非硬编码列序。
"""
import csv
from datetime import datetime
from typing import Optional

import openpyxl


def _to_float(val) -> float:
    """金额归一:支付宝是字符串,微信可能是 int/float,可能带 ¥ 或逗号。"""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("¥", "").replace(",", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_dt(val) -> Optional[datetime]:
    """时间归一:微信 openpyxl 已是 datetime;支付宝是 'YYYY-MM-DD HH:MM:SS' 字符串。"""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    s = str(val).strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _direction(shou_zhi: str) -> str:
    s = (shou_zhi or "").strip()
    if s == "支出":
        return "expense"
    if s == "收入":
        return "income"
    return "neutral"  # 支付宝「不计收支」/ 空


# ---------------------------------------------------------------------------
# 支付宝
# ---------------------------------------------------------------------------

def parse_alipay(path: str) -> list[dict]:
    """解析支付宝交易记录 CSV(GBK)。按列名定位列头,跳过说明/汇总行。"""
    text = open(path, "rb").read().decode("gbk", errors="replace")
    rows = list(csv.reader(text.splitlines()))

    # 定位列头行:含「交易号」的那一行
    header_idx = None
    for i, row in enumerate(rows):
        if any(c.strip() == "交易号" for c in row):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"支付宝账单未找到列头(交易号): {path}")

    header = [c.strip() for c in rows[header_idx]]
    col = {name: idx for idx, name in enumerate(header)}

    def get(row, name):
        idx = col.get(name)
        if idx is None or idx >= len(row):
            return ""
        return row[idx].strip()

    records = []
    for row in rows[header_idx + 1:]:
        if not row:
            continue
        biz_no = (row[0].strip() if row else "")
        # 跳过尾部汇总/分隔行:首格非交易号(数字流水号)
        if not biz_no or biz_no.startswith("---") or biz_no.startswith("共") \
                or "导出时间" in biz_no or "笔记录" in biz_no:
            continue

        amount = _to_float(get(row, "金额（元）"))
        shou_zhi = get(row, "收/支")
        status = get(row, "交易状态")
        txn_time = _parse_dt(get(row, "付款时间")) or _parse_dt(get(row, "交易创建时间"))
        if txn_time is None:
            continue  # 无任何可用时间,跳过

        # 标记不计入统计:已关闭/已退款,或 0 元担保(等待确认收货)
        excluded = 1 if (status in ("交易关闭", "退款成功") or amount <= 0) else 0

        records.append({
            "source": "alipay",
            "biz_no": biz_no,
            "txn_time": txn_time,
            "direction": _direction(shou_zhi),
            "amount": amount,
            "counterparty": get(row, "交易对方"),
            "product": get(row, "商品名称"),
            "raw_type": get(row, "类型"),
            "raw_origin": get(row, "交易来源地"),
            "status": status,
            "excluded": excluded,
        })
    return records


# ---------------------------------------------------------------------------
# 微信
# ---------------------------------------------------------------------------

def parse_wechat(path: str) -> list[dict]:
    """解析微信支付账单 xlsx。按列名定位列头,金额归一为 float。"""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    all_rows = [tuple(r) for r in ws.iter_rows(values_only=True)]
    wb.close()

    # 定位列头行:含「交易时间」的那一行
    header_idx = None
    for i, row in enumerate(all_rows):
        if any(c is not None and str(c).strip() == "交易时间" for c in row):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"微信账单未找到列头(交易时间): {path}")

    header = [(str(c).strip() if c is not None else "") for c in all_rows[header_idx]]
    col = {name: idx for idx, name in enumerate(header)}

    def get(row, name):
        idx = col.get(name)
        if idx is None or idx >= len(row):
            return ""
        v = row[idx]
        return "" if v is None else (v if isinstance(v, datetime) else str(v).strip())

    records = []
    for row in all_rows[header_idx + 1:]:
        if row is None or all(c is None for c in row):
            continue
        biz_no = get(row, "交易单号")
        if not biz_no:
            continue

        amount = _to_float(row[col["金额(元)"]] if "金额(元)" in col else None)
        shou_zhi = get(row, "收/支")
        status = get(row, "当前状态")
        raw_type = get(row, "交易类型")
        txn_time = _parse_dt(get(row, "交易时间"))
        if txn_time is None:
            continue

        # 标记不计入统计:状态或交易类型含「退款」
        excluded = 1 if ("退款" in (status or "") or "退款" in (raw_type or "")) else 0

        records.append({
            "source": "wechat",
            "biz_no": biz_no,
            "txn_time": txn_time,
            "direction": _direction(shou_zhi),
            "amount": amount,
            "counterparty": get(row, "交易对方"),
            "product": get(row, "商品"),
            "raw_type": raw_type,
            "raw_origin": get(row, "支付方式"),
            "status": status,
            "excluded": excluded,
        })
    return records


def parse_file(path: str) -> list[dict]:
    """按文件名/扩展名判定来源并解析。"""
    lower = path.lower()
    if lower.endswith(".csv") or "alipay" in lower or "支付宝" in path:
        return parse_alipay(path)
    if lower.endswith(".xlsx") or "wechat" in lower or "微信" in path:
        return parse_wechat(path)
    raise ValueError(f"无法判定账单来源(非 .csv/.xlsx): {path}")
