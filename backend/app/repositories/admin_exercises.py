from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise


class AdminExercisesRepository:
    """DB 접근만 담당 — commit 하지 않는다(트랜잭션은 service)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Exercise]:
        result = await self.db.execute(select(Exercise).order_by(Exercise.id))
        return list(result.scalars().all())
