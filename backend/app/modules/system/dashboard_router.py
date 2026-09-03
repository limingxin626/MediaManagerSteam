"""HTTP boundary for dashboard reports."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import get_db
from app.modules.system import service
from app.modules.system.schemas import DashboardStats, HeatmapResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)) -> DashboardStats:
    return service.dashboard_stats(db)


@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(db: Session = Depends(get_db)) -> HeatmapResponse:
    return service.heatmap(db)
