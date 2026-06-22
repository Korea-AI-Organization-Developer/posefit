from datetime import datetime
from decimal import Decimal

from app.models.enums import SessionStatus
from app.schemas.base import CamelModel


class EmbeddedExercise(CamelModel):
    id: int
    name_ko: str


class AdminSessionListItem(CamelModel):
    id: int
    exercise: EmbeddedExercise
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None
    score: Decimal | None
    rep_count: int | None
    hold_sec: int | None
    saved: bool


class AdminSessionPage(CamelModel):
    total: int
    page: int
    size: int
    items: list[AdminSessionListItem]
