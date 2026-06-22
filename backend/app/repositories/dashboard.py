from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workout import WorkoutSession


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recent_score(self, user_id: int) -> Decimal | None:
        """가장 최근 완료 세션의 점수."""
        result = await self.db.execute(
            select(WorkoutSession.score)
            .where(WorkoutSession.user_id == user_id, WorkoutSession.score.is_not(None))
            .order_by(WorkoutSession.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_weekly_sessions_count(self, user_id: int) -> int:
        """이번 주(월~일) 세션 수."""
        today = date.today()
        monday = today.toordinal() - today.weekday()
        week_start = datetime.fromordinal(monday).replace(tzinfo=timezone.utc)

        result = await self.db.execute(
            select(func.count(WorkoutSession.id)).where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.started_at >= week_start,
            )
        )
        return result.scalar_one() or 0

    async def get_lifetime_sessions_count(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(WorkoutSession.id)).where(WorkoutSession.user_id == user_id)
        )
        return result.scalar_one() or 0

    async def get_recent_sessions(self, user_id: int, limit: int = 5) -> list[WorkoutSession]:
        result = await self.db.execute(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user_id)
            .options(selectinload(WorkoutSession.exercise))
            .order_by(WorkoutSession.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
