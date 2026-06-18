from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.admin import AdminAccount
from app.schemas.admin_exercises import AdminExercise
from app.services.admin_exercises import AdminExercisesService

router = APIRouter(prefix="/admin", tags=["Admin Exercises"])


@router.get("/exercises", response_model=list[AdminExercise])
async def list_admin_exercises(
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminExercisesService(db).list_exercises()
