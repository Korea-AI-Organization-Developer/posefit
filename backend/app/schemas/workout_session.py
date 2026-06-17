from datetime import datetime
from decimal import Decimal

from app.models.enums import SessionStatus
from app.schemas.base import CamelModel


class WorkoutSessionCreateRequest(CamelModel):
    exercise_id: int
    started_at: datetime


class WorkoutSessionRead(CamelModel):
    id: int
    exercise_id: int
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None
    score: Decimal | None
    rep_count: int | None
    hold_sec: int | None
    saved: bool
    video_url: str | None
    created_at: datetime
