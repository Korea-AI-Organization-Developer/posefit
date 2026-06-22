from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SessionStatus, UserStatus
from app.models.mixins import KST
from app.models.user import User
from app.models.workout import WorkoutSession


def _to_kst_naive(dt: datetime) -> datetime:
    """UTC-aware datetime → KST naive (DB 저장 형식과 동일하게 맞춤)."""
    return dt.astimezone(KST).replace(tzinfo=None)


class AdminStatsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_users_by_status(self) -> dict[UserStatus, int]:
        result = await self.db.execute(
            select(User.status, func.count().label("cnt")).group_by(User.status)
        )
        return {row.status: row.cnt for row in result}

    async def count_total_sessions(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(WorkoutSession))
        return result.scalar_one()

    async def avg_score_completed(self) -> float | None:
        result = await self.db.execute(
            select(func.avg(WorkoutSession.score)).where(
                WorkoutSession.status == SessionStatus.completed
            )
        )
        value = result.scalar_one()
        return float(value) if value is not None else None

    async def timeseries(
        self, from_dt: datetime, to_dt: datetime
    ) -> dict[date, dict[str, int]]:
        from_kst = _to_kst_naive(from_dt)
        to_kst = _to_kst_naive(to_dt)

        signup_rows = await self.db.execute(
            select(func.date(User.created_at).label("d"), func.count().label("cnt"))
            .where(User.created_at.between(from_kst, to_kst))
            .group_by("d")
        )
        session_rows = await self.db.execute(
            select(
                func.date(WorkoutSession.started_at).label("d"),
                func.count().label("cnt"),
            )
            .where(WorkoutSession.started_at.between(from_kst, to_kst))
            .group_by("d")
        )

        data: dict[date, dict[str, int]] = {}
        cur = from_kst.date()
        end = to_kst.date()
        while cur <= end:
            data[cur] = {"signups": 0, "sessions": 0}
            cur += timedelta(days=1)

        for row in signup_rows:
            if row.d in data:
                data[row.d]["signups"] = row.cnt
        for row in session_rows:
            if row.d in data:
                data[row.d]["sessions"] = row.cnt

        return data
