from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserStatus
from app.repositories.admin_stats import AdminStatsRepository
from app.schemas.admin_stats import StatsOverview, StatsTimeseries, TimeseriesPoint


class AdminStatsService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminStatsRepository(db)

    async def get_timeseries(self, from_dt: datetime, to_dt: datetime) -> StatsTimeseries:
        data = await self.repo.timeseries(from_dt, to_dt)
        points = [
            TimeseriesPoint(date=d, signups=v["signups"], sessions=v["sessions"])
            for d, v in sorted(data.items())
        ]
        return StatsTimeseries(points=points)

    async def get_overview(self) -> StatsOverview:
        counts, total_sessions, avg_score = (
            await self.repo.count_users_by_status(),
            await self.repo.count_total_sessions(),
            await self.repo.avg_score_completed(),
        )
        return StatsOverview(
            total_users=sum(counts.values()),
            active_users=counts.get(UserStatus.active, 0),
            suspended_users=counts.get(UserStatus.suspended, 0),
            withdrawn_users=counts.get(UserStatus.withdrawn, 0),
            total_sessions=total_sessions,
            avg_score=avg_score,
        )
