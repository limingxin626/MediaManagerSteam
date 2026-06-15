from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Index, UniqueConstraint
from datetime import datetime

from app.models import Base


class Transaction(Base):
    """一笔账单流水(支付宝 / 微信导入)。source + biz_no 源内唯一,保证重复导入幂等。"""
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(16), nullable=False, index=True)        # alipay | wechat
    biz_no = Column(String(64), nullable=False)                    # 交易号 / 交易单号(源内唯一)
    txn_time = Column(DateTime, nullable=False, index=True)
    direction = Column(String(8), nullable=False, index=True)      # expense | income | neutral
    amount = Column(Float, nullable=False)                         # 单位:元
    counterparty = Column(String(256), nullable=True)              # 交易对方
    product = Column(Text, nullable=True)                          # 商品名称 / 商品
    category = Column(String(64), nullable=True, index=True)       # 自动分类结果
    raw_type = Column(String(64), nullable=True)                   # 交易类型 / 类型
    raw_origin = Column(String(64), nullable=True)                 # 交易来源地(支付宝特有)
    status = Column(String(64), nullable=True)                     # 原始状态文本
    excluded = Column(Integer, default=0, nullable=False)          # 1 = 退款/关闭/0元,默认不计统计
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "biz_no", name="uq_txn_source_bizno"),
        Index("ix_txn_time_dir", "txn_time", "direction"),
    )


class TxnCategoryRule(Base):
    """关键词分类规则:keyword 命中 交易对方+商品 文本即归入 category。priority 高者先匹配。"""
    __tablename__ = "txn_category_rule"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(128), nullable=False, index=True)
    category = Column(String(64), nullable=False)
    priority = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("keyword", name="uq_txn_rule_keyword"),
    )
