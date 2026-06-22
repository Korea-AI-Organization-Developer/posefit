from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise
from app.models.workout import WorkoutDailyStat


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_calendar(
        self, user_id: int, start_date: date, end_date: date
    ) -> list:
        """start_date ~ end_date 범위의 (stat_date, sessions_count, avg_score) 반환."""
        result = await self.db.execute(
            select(
                WorkoutDailyStat.stat_date,
                func.sum(WorkoutDailyStat.session_count).label("sessions_count"),
                func.avg(WorkoutDailyStat.avg_score).label("avg_score"),
            )
            .where(
                WorkoutDailyStat.user_id == user_id,
                WorkoutDailyStat.stat_date >= start_date,
                WorkoutDailyStat.stat_date <= end_date,
            )
            .group_by(WorkoutDailyStat.stat_date)
            .order_by(WorkoutDailyStat.stat_date)
        )
        return result.all()

    async def get_summary(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        exercise_id: int | None,
    ) -> list:
        """기간 내 (exercise_id, name_ko, sessions_count, total_duration_sec, avg_score, best_score) 반환."""
        filters = [
            WorkoutDailyStat.user_id == user_id,
            WorkoutDailyStat.stat_date >= start_date,
            WorkoutDailyStat.stat_date <= end_date,
        ]
        if exercise_id is not None:
            filters.append(WorkoutDailyStat.exercise_id == exercise_id)

        result = await self.db.execute(
            select(
                WorkoutDailyStat.exercise_id,
                Exercise.name_ko,
                func.sum(WorkoutDailyStat.session_count).label("sessions_count"),
                func.sum(WorkoutDailyStat.total_duration_sec).label("total_duration_sec"),
                func.avg(WorkoutDailyStat.avg_score).label("avg_score"),
                func.max(WorkoutDailyStat.best_score).label("best_score"),
            )
            .join(Exercise, Exercise.id == WorkoutDailyStat.exercise_id)
            .where(*filters)
            .group_by(WorkoutDailyStat.exercise_id, Exercise.name_ko)
        )
        return result.all()

    async def get_score_trend(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        exercise_id: int | None,
    ) -> list:
        """(exercise_id, name_ko, stat_date, avg_score) 행 목록 반환."""
        filters = [
            WorkoutDailyStat.user_id == user_id,
            WorkoutDailyStat.stat_date >= start_date,
            WorkoutDailyStat.stat_date <= end_date,
            WorkoutDailyStat.avg_score.isnot(None),
        ]
        if exercise_id is not None:
            filters.append(WorkoutDailyStat.exercise_id == exercise_id)

        result = await self.db.execute(
            select(
                WorkoutDailyStat.exercise_id,
                Exercise.name_ko,
                WorkoutDailyStat.stat_date,
                WorkoutDailyStat.avg_score,
            )
            .join(Exercise, Exercise.id == WorkoutDailyStat.exercise_id)
            .where(*filters)
            .order_by(WorkoutDailyStat.exercise_id, WorkoutDailyStat.stat_date)
        )
        return result.all()
