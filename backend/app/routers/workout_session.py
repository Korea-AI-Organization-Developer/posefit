from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.workout import NextSessionResponse, SaveSessionResponse, StopSessionResponse
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


@router.post("/{session_id}:save", response_model=SaveSessionResponse)
async def save_workout_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await WorkoutSessionService(db).save_video(session_id, user.id)
    return SaveSessionResponse(success=True)


@router.post("/{session_id}:discard", response_model=SaveSessionResponse)
async def discard_workout_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await WorkoutSessionService(db).discard_session(session_id, user.id)
    return SaveSessionResponse(success=True)


@router.post("/{session_id}:next", response_model=NextSessionResponse, status_code=201)
async def next_workout_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_session = await WorkoutSessionService(db).next_session(session_id, user.id)
    return NextSessionResponse(
        id=new_session.id,
        exercise_id=new_session.exercise_id,
        status=new_session.status,
    )
