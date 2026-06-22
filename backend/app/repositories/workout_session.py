from datetime import datetime

from app.models.mixins import KST

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SessionStatus
from app.models.workout import WorkoutSession


class WorkoutSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        exercise_id: int,
        started_at: datetime,
        ended_at: datetime,
        video_url: str,
        json_url: str | None = None,
    ) -> WorkoutSession:
        session = WorkoutSession(
            user_id=user_id,
            exercise_id=exercise_id,
            started_at=started_at,
            ended_at=ended_at,
            status=SessionStatus.completed,
            video_url=video_url,
            json_url=json_url,
            saved=False,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def create_in_progress(
        self, user_id: int, exercise_id: int
    ) -> WorkoutSession:
        session = WorkoutSession(
            user_id=user_id,
            exercise_id=exercise_id,
            status=SessionStatus.in_progress,
            started_at=datetime.now(KST),
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_id(self, session_id: int) -> WorkoutSession | None:
        result = await self.db.execute(
            select(WorkoutSession).where(WorkoutSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def update_saved(self, session: WorkoutSession, video_url: str) -> None:
        session.video_url = video_url
        session.saved = True

    async def delete(self, session: WorkoutSession) -> None:
        await self.db.delete(session)
