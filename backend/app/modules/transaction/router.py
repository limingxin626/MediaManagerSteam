"""Transaction 只读 router:列表(游标分页+过滤+排序)、月度汇总、可用月份。

游标格式: "{primary}|{id}",primary 由 sort 决定(time=ISO 时间, amount=数字)。
按 (primary, id) 复合排序,id 兜底同值稳定性,跟 media 复合游标范式一致。
"""
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import get_db
from app.modules.transaction.schemas import (
    MonthBucket,
    MonthlySummary,
    RangeSummary,
    TransactionListResponse,
    TransactionOut,
    TransactionUpdate,
)
from app.modules.transaction import service as txn_svc

router = APIRouter(prefix="/transactions", tags=["transactions"])

SortField = Literal["time", "amount"]
SortOrder = Literal["asc", "desc"]


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    cursor: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    year: Optional[int] = None,
    month: Optional[int] = Query(None, ge=1, le=12),
    from_year: Optional[int] = Query(None, ge=2000, le=2100),
    from_month: Optional[int] = Query(None, ge=1, le=12),
    to_year: Optional[int] = Query(None, ge=2000, le=2100),
    to_month: Optional[int] = Query(None, ge=1, le=12),
    category: Optional[str] = None,
    direction: Optional[str] = None,
    excluded: Optional[int] = Query(None, ge=0, le=1),
    sort: SortField = "time",
    order: SortOrder = "desc",
    db: Session = Depends(get_db),
):
    """按 (sort_col, id) 游标分页。时间窗口优先用 from_*/to_* 月份范围(闭区间),否则用 year/month 单月。"""
    try:
        return txn_svc.list_transactions(db, cursor=cursor, limit=limit, year=year, month=month, from_year=from_year, from_month=from_month, to_year=to_year, to_month=to_month, category=category, direction=direction, excluded=excluded, sort=sort, order=order)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/summary/monthly", response_model=MonthlySummary)
def monthly(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    direction: str = "expense",
    db: Session = Depends(get_db),
):
    data = txn_svc.monthly_summary(db, year, month, direction)
    return MonthlySummary(**data)


@router.get("/summary/range", response_model=RangeSummary)
def range_summary(
    from_year: int = Query(..., ge=2000, le=2100),
    from_month: int = Query(..., ge=1, le=12),
    to_year: int = Query(..., ge=2000, le=2100),
    to_month: int = Query(..., ge=1, le=12),
    direction: str = "expense",
    db: Session = Depends(get_db),
):
    """月份范围 [from, to] 闭区间的支出汇总;起止反了自动 swap。"""
    data = txn_svc.range_summary(db, from_year, from_month, to_year, to_month, direction)
    return RangeSummary(**data)


@router.get("/months", response_model=List[MonthBucket])
def list_months(db: Session = Depends(get_db)):
    """所有有数据的 (year, month),倒序;附带笔数与计入支出。前端做月份选择器用。"""
    return txn_svc.list_months(db)


@router.get("/categories", response_model=List[str])
def list_categories(db: Session = Depends(get_db)):
    """已出现的全部 category,按使用频次降序。"""
    return txn_svc.list_categories(db)


@router.patch("/{txn_id}", response_model=TransactionOut)
def update_transaction(
    txn_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
):
    """部分更新单条流水。只允许改 category / excluded / counterparty / product 四个字段。"""
    data = payload.model_dump(exclude_unset=True)
    try: return txn_svc.update_transaction(db, txn_id, data)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
