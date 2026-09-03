from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


IssueStatus = Literal["doing", "done", "archived", "abandoned"]


class IssueCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    description: Optional[str] = None
    status: IssueStatus = "doing"


class IssueUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    description: Optional[str] = None


class IssueMove(BaseModel):
    status: IssueStatus
    position: int = Field(..., ge=0)


class IssueOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: IssueStatus
    position: int
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class IssueBoard(BaseModel):
    doing: List[IssueOut]
    done: List[IssueOut]
    archived: List[IssueOut]
    abandoned: List[IssueOut]
