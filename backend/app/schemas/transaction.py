"""Transaction 相关 schema。只读用,不含写入。"""
from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


Direction = Literal["expense", "income", "neutral"]


class TransactionOut(BaseModel):
    id: int
    source: str
    biz_no: str
    txn_time: datetime
    direction: Direction
    amount: float
    counterparty: Optional[str] = None
    product: Optional[str] = None
    category: Optional[str] = None
    raw_type: Optional[str] = None
    raw_origin: Optional[str] = None
    status: Optional[str] = None
    excluded: int

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: List[TransactionOut]
    next_cursor: Optional[str] = None
    has_more: bool


class CategorySlot(BaseModel):
    count: int
    amount: float


class MonthlySummary(BaseModel):
    year: int
    month: int
    total: float
    by_category: Dict[str, CategorySlot]


class MonthBucket(BaseModel):
    """有数据的月份(用于前端月份选择器)。"""
    year: int
    month: int
    count: int
    total_expense: float
