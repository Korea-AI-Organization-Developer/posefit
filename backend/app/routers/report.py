from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import CalendarResponse, ReportPeriod, ReportSummary, ScoreTrendResponse
from app.services.report import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/calendar", response_model=CalendarResponse)
async def get_activity_calendar(
    days: int = Query(..., ge=7, le=90, description="오늘부터 거슬러 N일"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).get_calendar(user.id, days)


@router.get("/summary", response_model=ReportSummary)
async def get_report_summary(
    period: ReportPeriod = Query(...),
    reference_date: date | None = Query(default=None, alias="referenceDate"),
    exercise_id: int | None = Query(default=None, alias="exerciseId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_created_at = user.created_at.date()
    return await ReportService(db).get_summary(
        user.id, period, reference_date, exercise_id, user_created_at
    )


@router.get("/score-trend", response_model=ScoreTrendResponse)
async def get_score_trend(
    days: int = Query(..., enum=[7, 30, 90]),
    exercise_id: int | None = Query(default=None, alias="exerciseId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService(db).get_score_trend(user.id, days, exercise_id)
