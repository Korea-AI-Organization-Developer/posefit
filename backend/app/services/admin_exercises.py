from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.admin_exercises import AdminExercisesRepository
from app.schemas.admin_exercises import AdminExercise


class AdminExercisesService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminExercisesRepository(db)

    async def list_exercises(self) -> list[AdminExercise]:
        exercises = await self.repo.list_all()
        return [AdminExercise.model_validate(ex) for ex in exercises]
