from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.workout import StopSessionResponse
from app.services.workout_session import WorkoutSessionService

router = APIRouter(prefix="/workout-sessions", tags=["Sessions"])


@router.post(":stop", response_model=StopSessionResponse)
async def stop_workout_session(
    exercise_id: int = Form(...),
    start_at: datetime = Form(...),
    end_at: datetime = Form(...),
    video: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkoutSessionService(db).stop(
        user_id=user.id,
        exercise_id=exercise_id,
        start_at=start_at,
        end_at=end_at,
        video=video,
    )
