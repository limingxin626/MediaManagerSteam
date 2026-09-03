"""Schemas for application-level reporting."""
from typing import List
from pydantic import BaseModel


class DashboardStats(BaseModel):
    message_count: int
    media_count: int
    media_this_month: int
    todo_doing_count: int


class HeatmapDay(BaseModel):
    date: str
    count: int


class HeatmapResponse(BaseModel):
    start_date: str
    end_date: str
    days: List[HeatmapDay]
