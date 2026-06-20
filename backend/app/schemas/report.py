from datetime import date
from decimal import Decimal
from enum import Enum

from app.schemas.base import CamelModel


# ─── Calendar ───
class CalendarDay(CamelModel):
    date: date
    sessions_count: int
    avg_score: Decimal | None = None


class CalendarResponse(CamelModel):
    days: list[CalendarDay]


# ─── Summary ───
class ReportPeriod(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    cumulative = "cumulative"


class BestExercise(CamelModel):
    id: int
    name_ko: str
    best_score: Decimal


class ReportSummary(CamelModel):
    period: ReportPeriod
    period_start: date
    period_end: date
    sessions_count: int
    total_duration_sec: int
    avg_score: Decimal | None = None
    best_exercise: BestExercise | None = None


# ─── Score Trend ───
class EmbeddedExercise(CamelModel):
    id: int
    name_ko: str


class ScoreTrendPoint(CamelModel):
    date: date
    avg_score: Decimal


class ScoreTrendSeries(CamelModel):
    exercise: EmbeddedExercise
    points: list[ScoreTrendPoint]


class ScoreTrendResponse(CamelModel):
    series: list[ScoreTrendSeries]


# ─── Evaluation ───
class EvaluationMessageType(str, Enum):
    positive = "positive"
    warning = "warning"
    tip = "tip"


class EvaluationMessage(CamelModel):
    type: EvaluationMessageType
    text: str


class EvaluationResponse(CamelModel):
    period: ReportPeriod
    exercise_id: int | None = None
    messages: list[EvaluationMessage]


# ─── Overview (팝업) ───
class ReportOverview(CamelModel):
    summary: ReportSummary          # 누적 요약
    calendar: CalendarResponse      # 최근 30일 캘린더
    score_trend: ScoreTrendResponse # 최근 90일 점수 추이
    evaluation: EvaluationResponse  # 종합 평가
