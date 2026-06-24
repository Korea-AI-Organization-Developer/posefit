from datetime import datetime

from app.models.mixins import KST

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

    async def list_saved(
        self,
        user_id: int,
        exercise_id: int | None = None,
        cursor: int | None = None,
        limit: int = 6,
    ) -> list[WorkoutSession]:
        q = (
            select(WorkoutSession)
            .options(selectinload(WorkoutSession.exercise))
            .where(WorkoutSession.user_id == user_id, WorkoutSession.saved == True)  # noqa: E712
        )
        if exercise_id is not None:
            q = q.where(WorkoutSession.exercise_id == exercise_id)
        if cursor is not None:
            q = q.where(WorkoutSession.id < cursor)
        q = q.order_by(WorkoutSession.id.desc()).limit(limit + 1)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_scores_by_ids(self, session_ids: list[int]) -> dict[int, float | None]:
        if not session_ids:
            return {}
        result = await self.db.execute(
            select(WorkoutSession.id, WorkoutSession.score)
            .where(WorkoutSession.id.in_(session_ids))
        )
        return {
            row[0]: float(row[1]) if row[1] is not None else None
            for row in result.all()
        }

    async def delete(self, session: WorkoutSession) -> None:
        await self.db.delete(session)
