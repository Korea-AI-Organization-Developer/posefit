from datetime import datetime

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
    ) -> WorkoutSession:
        session = WorkoutSession(
            user_id=user_id,
            exercise_id=exercise_id,
            started_at=started_at,
            ended_at=ended_at,
            status=SessionStatus.completed,
            video_url=video_url,
            saved=True,
        )
        self.db.add(session)
        await self.db.flush()
        return session
