from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.admin import AdminAccount
from app.schemas.admin_stats import StatsOverview, StatsTimeseries
from app.services.admin_stats import AdminStatsService

router = APIRouter(prefix="/admin", tags=["Admin Stats"])


@router.get("/stats/overview", response_model=StatsOverview)
async def get_stats_overview(
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminStatsService(db).get_overview()


@router.get("/stats/timeseries", response_model=StatsTimeseries)
async def get_stats_timeseries(
    from_dt: datetime = Query(alias="from"),
    to_dt: datetime = Query(alias="to"),
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminStatsService(db).get_timeseries(from_dt, to_dt)
