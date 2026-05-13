from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models import Base


class Issue(Base):
    __tablename__ = "issue"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="doing", index=True)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    messages = relationship("Message", back_populates="issue")

    __table_args__ = (
        Index("ix_issue_status_position", "status", "position"),
    )
