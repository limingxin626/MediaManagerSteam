from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


TodoStatus = Literal["pending", "doing", "done"]


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    status: TodoStatus = "pending"


class TodoUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)


class TodoMove(BaseModel):
    status: TodoStatus
    position: int = Field(..., ge=0)


class TodoOut(BaseModel):
    id: int
    title: str
    status: TodoStatus
    position: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TodoBoard(BaseModel):
    pending: List[TodoOut]
    doing: List[TodoOut]
    done: List[TodoOut]
