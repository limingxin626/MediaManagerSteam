from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime

from app.models import Base


class Todo(Base):
    __tablename__ = "todo"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    status = Column(String(16), nullable=False, default="pending", index=True)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_todo_status_position", "status", "position"),
    )
