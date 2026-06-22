from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dashboard import DashboardRepository
from app.schemas.dashboard import DashboardResponse, EmbeddedExercise, RecentSession


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.repo = DashboardRepository(db)

    async def get_dashboard(self, user_id: int) -> DashboardResponse:
        recent_score, weekly_count, lifetime_count, sessions = await _gather(
            self.repo.get_recent_score(user_id),
            self.repo.get_weekly_sessions_count(user_id),
            self.repo.get_lifetime_sessions_count(user_id),
            self.repo.get_recent_sessions(user_id),
        )

        recent_sessions = [
            RecentSession(
                id=s.id,
                exercise=EmbeddedExercise(id=s.exercise.id, name_ko=s.exercise.name_ko),
                status=s.status,
                started_at=s.started_at,
                ended_at=s.ended_at,
                duration_sec=(
                    int((s.ended_at - s.started_at).total_seconds()) if s.ended_at else None
                ),
                score=s.score,
                rep_count=s.rep_count,
                saved=s.saved,
            )
            for s in sessions
        ]

        return DashboardResponse(
            recent_score=recent_score,
            weekly_sessions_count=weekly_count,
            lifetime_sessions_count=lifetime_count,
            recent_sessions=recent_sessions,
        )


async def _gather(*coros):
    import asyncio
    return await asyncio.gather(*coros)
