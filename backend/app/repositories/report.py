from datetime import date

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SessionStatus
from app.models.exercise import Exercise
from app.models.workout import WorkoutDailyStat, WorkoutSession


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_calendar(
        self, user_id: int, start_date: date, end_date: date
    ) -> list:
        """start_date ~ end_date 범위의 (stat_date, sessions_count, avg_score) 반환.
        workout_daily_stats 가 업데이트되지 않으므로 workout_sessions 를 직접 집계한다."""
        result = await self.db.execute(
            select(
                func.date(WorkoutSession.started_at).label("stat_date"),
                func.count(WorkoutSession.id).label("sessions_count"),
                func.avg(WorkoutSession.score).label("avg_score"),
            )
            .where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.status == SessionStatus.completed,
                func.date(WorkoutSession.started_at) >= start_date,
                func.date(WorkoutSession.started_at) <= end_date,
            )
            .group_by(func.date(WorkoutSession.started_at))
            .order_by(func.date(WorkoutSession.started_at))
        )
        return result.all()

    async def get_daily_metrics(
        self, user_id: int, exercise_id: int | None, start_date: date, end_date: date
    ) -> list:
        """장기 추세 계산용. 날짜별 (stat_date, session_count, total_duration_sec, avg_score) 오름차순."""
        filters = [
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.completed,
            func.date(WorkoutSession.started_at) >= start_date,
            func.date(WorkoutSession.started_at) <= end_date,
        ]
        if exercise_id is not None:
            filters.append(WorkoutSession.exercise_id == exercise_id)

        result = await self.db.execute(
            select(
                func.date(WorkoutSession.started_at).label("stat_date"),
                func.count(WorkoutSession.id).label("session_count"),
                func.sum(
                    func.timestampdiff(text("SECOND"), WorkoutSession.started_at, WorkoutSession.ended_at)
                ).label("total_duration_sec"),
                func.avg(WorkoutSession.score).label("avg_score"),
            )
            .where(*filters)
            .group_by(func.date(WorkoutSession.started_at))
            .order_by(func.date(WorkoutSession.started_at))
        )
        return result.all()

    async def get_calendar_durations(
        self, user_id: int, start_date: date, end_date: date
    ) -> list:
        """캘린더 칼로리 계산용. 날짜·종목별 (stat_date, name_en, exercise_type, total_duration_sec) 반환."""
        result = await self.db.execute(
            select(
                func.date(WorkoutSession.started_at).label("stat_date"),
                Exercise.name_en,
                Exercise.exercise_type,
                func.sum(
                    func.timestampdiff(text("SECOND"), WorkoutSession.started_at, WorkoutSession.ended_at)
                ).label("total_duration_sec"),
            )
            .join(Exercise, Exercise.id == WorkoutSession.exercise_id)
            .where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.status == SessionStatus.completed,
                func.date(WorkoutSession.started_at) >= start_date,
                func.date(WorkoutSession.started_at) <= end_date,
            )
            .group_by(func.date(WorkoutSession.started_at), Exercise.name_en, Exercise.exercise_type)
            .order_by(func.date(WorkoutSession.started_at))
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
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.completed,
            func.date(WorkoutSession.started_at) >= start_date,
            func.date(WorkoutSession.started_at) <= end_date,
        ]
        if exercise_id is not None:
            filters.append(WorkoutSession.exercise_id == exercise_id)

        result = await self.db.execute(
            select(
                WorkoutSession.exercise_id,
                Exercise.name_ko,
                func.count(WorkoutSession.id).label("sessions_count"),
                func.sum(
                    func.timestampdiff(text("SECOND"), WorkoutSession.started_at, WorkoutSession.ended_at)
                ).label("total_duration_sec"),
                func.avg(WorkoutSession.score).label("avg_score"),
                func.max(WorkoutSession.score).label("best_score"),
            )
            .join(Exercise, Exercise.id == WorkoutSession.exercise_id)
            .where(*filters)
            .group_by(WorkoutSession.exercise_id, Exercise.name_ko)
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
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.completed,
            WorkoutSession.score.isnot(None),
            func.date(WorkoutSession.started_at) >= start_date,
            func.date(WorkoutSession.started_at) <= end_date,
        ]
        if exercise_id is not None:
            filters.append(WorkoutSession.exercise_id == exercise_id)

        result = await self.db.execute(
            select(
                WorkoutSession.exercise_id,
                Exercise.name_ko,
                func.date(WorkoutSession.started_at).label("stat_date"),
                func.avg(WorkoutSession.score).label("avg_score"),
            )
            .join(Exercise, Exercise.id == WorkoutSession.exercise_id)
            .where(*filters)
            .group_by(WorkoutSession.exercise_id, Exercise.name_ko, func.date(WorkoutSession.started_at))
            .order_by(WorkoutSession.exercise_id, func.date(WorkoutSession.started_at))
        )
        return result.all()
