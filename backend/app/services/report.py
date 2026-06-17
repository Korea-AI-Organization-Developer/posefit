from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.report import ReportRepository
from app.schemas.report import (
    BestExercise,
    CalendarDay,
    CalendarResponse,
    EmbeddedExercise,
    ReportPeriod,
    ReportSummary,
    ScoreTrendPoint,
    ScoreTrendResponse,
    ScoreTrendSeries,
)


class ReportService:
    def __init__(self, db: AsyncSession):
        self.repo = ReportRepository(db)

    async def get_calendar(self, user_id: int, days: int) -> CalendarResponse:
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        rows = await self.repo.get_calendar(user_id, start_date, today)
        stat_map = {row.stat_date: row for row in rows}

        day_list = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            row = stat_map.get(d)
            day_list.append(
                CalendarDay(
                    date=d,
                    sessions_count=int(row.sessions_count) if row else 0,
                    avg_score=row.avg_score if row else None,
                )
            )
        return CalendarResponse(days=day_list)

    async def get_summary(
        self,
        user_id: int,
        period: ReportPeriod,
        reference_date: date | None,
        exercise_id: int | None,
        user_created_at: date,
    ) -> ReportSummary:
        today = date.today()
        ref = reference_date or today

        if period == ReportPeriod.day:
            start, end = ref, ref
        elif period == ReportPeriod.week:
            start = ref - timedelta(days=ref.weekday())  # 월요일
            end = start + timedelta(days=6)
        elif period == ReportPeriod.month:
            start = ref.replace(day=1)
            next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
            end = next_month - timedelta(days=1)
        else:  # cumulative
            start, end = user_created_at, today

        rows = await self.repo.get_summary(user_id, start, end, exercise_id)

        total_sessions = sum(int(r.sessions_count) for r in rows)
        total_duration = sum(int(r.total_duration_sec) for r in rows)

        # 전체 avg_score: 세션 수 가중 평균
        weighted_sum = sum(
            float(r.avg_score) * int(r.sessions_count)
            for r in rows
            if r.avg_score is not None
        )
        scored_sessions = sum(int(r.sessions_count) for r in rows if r.avg_score is not None)
        avg_score = Decimal(str(round(weighted_sum / scored_sessions, 2))) if scored_sessions else None

        # best_exercise: best_score 최고 종목
        best_row = max(
            (r for r in rows if r.best_score is not None),
            key=lambda r: r.best_score,
            default=None,
        )
        best_exercise = (
            BestExercise(id=best_row.exercise_id, name_ko=best_row.name_ko, best_score=best_row.best_score)
            if best_row
            else None
        )

        return ReportSummary(
            period=period,
            period_start=start,
            period_end=end,
            sessions_count=total_sessions,
            total_duration_sec=total_duration,
            avg_score=avg_score,
            best_exercise=best_exercise,
        )

    async def get_score_trend(
        self,
        user_id: int,
        days: int,
        exercise_id: int | None,
    ) -> ScoreTrendResponse:
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        rows = await self.repo.get_score_trend(user_id, start_date, today, exercise_id)

        # exercise_id별로 그룹핑
        series_map: dict[int, ScoreTrendSeries] = {}
        for row in rows:
            if row.exercise_id not in series_map:
                series_map[row.exercise_id] = ScoreTrendSeries(
                    exercise=EmbeddedExercise(id=row.exercise_id, name_ko=row.name_ko),
                    points=[],
                )
            series_map[row.exercise_id].points.append(
                ScoreTrendPoint(date=row.stat_date, avg_score=row.avg_score)
            )

        return ScoreTrendResponse(series=list(series_map.values()))
