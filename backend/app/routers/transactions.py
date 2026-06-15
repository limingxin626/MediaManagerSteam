"""Transaction 只读 router:列表(游标分页+过滤+排序)、月度汇总、可用月份。

游标格式: "{primary}|{id}",primary 由 sort 决定(time=ISO 时间, amount=数字)。
按 (primary, id) 复合排序,id 兜底同值稳定性,跟 media 复合游标范式一致。
"""
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models import Transaction, get_db
from app.schemas.transaction import (
    MonthBucket,
    MonthlySummary,
    TransactionListResponse,
    TransactionOut,
)
from app.services import transaction_service as txn_svc

router = APIRouter(prefix="/transactions", tags=["transactions"])

SortField = Literal["time", "amount"]
SortOrder = Literal["asc", "desc"]


def _sort_column(sort: SortField):
    return Transaction.txn_time if sort == "time" else Transaction.amount


def _parse_primary(sort: SortField, raw: str):
    if sort == "time":
        return datetime.fromisoformat(raw)
    return float(raw)


def _format_primary(sort: SortField, row: Transaction) -> str:
    if sort == "time":
        return row.txn_time.isoformat()
    return str(row.amount)


def _parse_cursor(cursor: Optional[str], sort: SortField):
    if not cursor:
        return None
    try:
        primary_str, id_str = cursor.split("|", 1)
        return _parse_primary(sort, primary_str), int(id_str)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail=f"invalid cursor: {cursor}")


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    cursor: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    year: Optional[int] = None,
    month: Optional[int] = Query(None, ge=1, le=12),
    category: Optional[str] = None,
    direction: Optional[str] = None,
    excluded: Optional[int] = Query(None, ge=0, le=1),
    sort: SortField = "time",
    order: SortOrder = "desc",
    db: Session = Depends(get_db),
):
    """按 (sort_col, id) 游标分页,order 控制升降序。year/month 为月窗口过滤。"""
    q = db.query(Transaction)

    if year is not None and month is not None:
        start = datetime(year, month, 1)
        end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        q = q.filter(Transaction.txn_time >= start, Transaction.txn_time < end)
    elif year is not None:
        q = q.filter(Transaction.txn_time >= datetime(year, 1, 1),
                     Transaction.txn_time < datetime(year + 1, 1, 1))

    if category is not None:
        q = q.filter(Transaction.category == category)
    if direction is not None:
        q = q.filter(Transaction.direction == direction)
    if excluded is not None:
        q = q.filter(Transaction.excluded == excluded)

    sort_col = _sort_column(sort)
    descending = order == "desc"

    parsed = _parse_cursor(cursor, sort)
    if parsed is not None:
        primary, cid = parsed
        if descending:
            q = q.filter(
                (sort_col < primary) | ((sort_col == primary) & (Transaction.id < cid))
            )
        else:
            q = q.filter(
                (sort_col > primary) | ((sort_col == primary) & (Transaction.id > cid))
            )

    if descending:
        q = q.order_by(sort_col.desc(), Transaction.id.desc())
    else:
        q = q.order_by(sort_col.asc(), Transaction.id.asc())

    rows = q.limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = f"{_format_primary(sort, rows[-1])}|{rows[-1].id}" if has_more and rows else None

    return TransactionListResponse(
        items=[TransactionOut.model_validate(r) for r in rows],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/summary/monthly", response_model=MonthlySummary)
def monthly(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    direction: str = "expense",
    db: Session = Depends(get_db),
):
    data = txn_svc.monthly_summary(db, year, month, direction)
    return MonthlySummary(**data)


@router.get("/months", response_model=List[MonthBucket])
def list_months(db: Session = Depends(get_db)):
    """所有有数据的 (year, month),倒序;附带笔数与计入支出。前端做月份选择器用。"""
    ym = func.strftime("%Y-%m", Transaction.txn_time).label("ym")
    expense_amt = case(
        ((Transaction.excluded == 0) & (Transaction.direction == "expense"),
         Transaction.amount),
        else_=0.0,
    )
    rows = (
        db.query(ym, func.count(Transaction.id), func.sum(expense_amt))
        .group_by(ym)
        .order_by(ym.desc())
        .all()
    )
    out: list[MonthBucket] = []
    for ym_str, cnt, total in rows:
        if not ym_str:
            continue
        y, m = ym_str.split("-")
        out.append(MonthBucket(
            year=int(y), month=int(m), count=int(cnt),
            total_expense=float(total or 0),
        ))
    return out


@router.get("/categories", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    """已出现的全部 category,按使用频次降序。"""
    rows = (
        db.query(Transaction.category, func.count(Transaction.id))
        .group_by(Transaction.category)
        .order_by(func.count(Transaction.id).desc())
        .all()
    )
    return [c for c, _ in rows if c]
