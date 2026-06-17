from datetime import datetime
from decimal import Decimal

from app.models.enums import SessionStatus
from app.schemas.base import CamelModel


class EmbeddedExercise(CamelModel):
    id: int
    name_ko: str


class RecentSession(CamelModel):
    id: int
    exercise: EmbeddedExercise
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None
    duration_sec: int | None
    score: Decimal | None
    rep_count: int | None
    saved: bool


class DashboardResponse(CamelModel):
    recent_score: Decimal | None
    weekly_sessions_count: int
    lifetime_sessions_count: int
    recent_sessions: list[RecentSession]
