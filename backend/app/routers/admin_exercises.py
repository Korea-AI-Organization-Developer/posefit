from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.admin import AdminAccount
from app.schemas.admin_exercises import AdminExercise, AdminExerciseCreateRequest, AdminExerciseUpdateRequest
from app.services.admin_exercises import AdminExercisesService

router = APIRouter(prefix="/admin", tags=["Admin Exercises"])


@router.get("/exercises", response_model=list[AdminExercise])
async def list_admin_exercises(
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminExercisesService(db).list_exercises()


@router.post("/exercises", response_model=AdminExercise, status_code=201)
async def create_admin_exercise(
    body: AdminExerciseCreateRequest,
    request: Request,
    admin: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await AdminExercisesService(db).create_exercise(body, admin.id, ip)


@router.patch("/exercises/{exercise_id}", response_model=AdminExercise)
async def update_admin_exercise(
    exercise_id: int,
    body: AdminExerciseUpdateRequest,
    request: Request,
    admin: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await AdminExercisesService(db).update_exercise(exercise_id, body, admin.id, ip)
