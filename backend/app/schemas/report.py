from datetime import date
from decimal import Decimal
from enum import Enum

from app.schemas.base import CamelModel


# ─── Calendar ───
class CalendarDay(CamelModel):
    date: date
    sessions_count: int
    avg_score: Decimal | None = None
    calories: float = 0  # 해당 날짜 소모 칼로리(kcal). 캘린더 색상 농도의 기준.


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


class EvaluationSource(str, Enum):
    ai = "ai"      # LangGraph LLM 기반 종합 평가
    rule = "rule"  # 규칙 기반 폴백


class EvaluationResponse(CamelModel):
    period: ReportPeriod
    exercise_id: int | None = None
    messages: list[EvaluationMessage]
    # summary: AI 평가 시 LLM 이 작성한 2~3문장 종합 요약(규칙 기반이면 빈 문자열).
    summary: str = ""
    source: EvaluationSource = EvaluationSource.rule


# ─── Overview (팝업) ───
class ReportOverview(CamelModel):
    summary: ReportSummary          # 누적 요약
    calendar: CalendarResponse      # 최근 30일 캘린더
    score_trend: ScoreTrendResponse # 최근 90일 점수 추이
    evaluation: EvaluationResponse  # 종합 평가
