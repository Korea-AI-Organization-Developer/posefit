from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.report import ReportRepository
from app.repositories.feedback import FeedbackRepository
from app.repositories.user import UserRepository
import asyncio
import logging

from app.schemas.report import (
    BestExercise,
    CalendarDay,
    CalendarResponse,
    EmbeddedExercise,
    EvaluationMessage,
    EvaluationMessageType,
    EvaluationResponse,
    EvaluationSource,
    ReportOverview,
    ReportPeriod,
    ReportSummary,
    ScoreTrendPoint,
    ScoreTrendResponse,
    ScoreTrendSeries,
)

logger = logging.getLogger(__name__)

# LangGraph 종합 평가 최대 대기(초). 초과 시 규칙 기반으로 폴백한다.
_AI_EVALUATION_TIMEOUT_SEC = 20

# 칼로리 계산용 운동별 MET (kcal = MET × 체중kg × 시간h).
# workout_calendar.html 의 per-rep 계수를 MET 로 환산한 값.
_MET_BY_KEYWORD = {
    "lunge": 4.5,
    "plank": 3.0,
    "push": 8.0,      # push-up
    "overhead": 6.0,
    "press": 6.0,
}
_DEFAULT_WEIGHT_KG = 70.0  # 체중 미입력 시 기본값(레퍼런스와 동일)


def _met_for(name_en: str | None, exercise_type) -> float:
    """종목명(영문) 키워드로 MET 결정. 못 찾으면 운동 타입으로 폴백."""
    name = (name_en or "").lower()
    for keyword, met in _MET_BY_KEYWORD.items():
        if keyword in name:
            return met
    type_value = getattr(exercise_type, "value", exercise_type)
    return 3.0 if type_value == "static" else 5.0  # static(정적)=3.0, dynamic(동적)=5.0


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReportRepository(db)

    async def get_calendar(self, user_id: int, days: int) -> CalendarResponse:
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        rows = await self.repo.get_calendar(user_id, start_date, today)
        stat_map = {row.stat_date: row for row in rows}

        # 날짜별 소모 칼로리 = Σ(종목 MET × 체중 × 운동시간h)
        weight = await self._get_user_weight(user_id)
        duration_rows = await self.repo.get_calendar_durations(user_id, start_date, today)
        calorie_map: dict[date, float] = {}
        for row in duration_rows:
            met = _met_for(row.name_en, row.exercise_type)
            hours = int(row.total_duration_sec or 0) / 3600
            calorie_map[row.stat_date] = calorie_map.get(row.stat_date, 0.0) + met * weight * hours

        day_list = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            row = stat_map.get(d)
            day_list.append(
                CalendarDay(
                    date=d,
                    sessions_count=int(row.sessions_count) if row else 0,
                    avg_score=row.avg_score if row else None,
                    calories=round(calorie_map.get(d, 0.0), 1),
                )
            )
        return CalendarResponse(days=day_list)

    async def _get_user_weight(self, user_id: int) -> float:
        """사용자 체중(kg). 미입력이면 기본값."""
        detail = await UserRepository(self.db).get_detail(user_id)
        if detail and detail.weight:
            return float(detail.weight)
        return _DEFAULT_WEIGHT_KG

    async def get_summary(
        self,
        user_id: int,
        period: ReportPeriod,
        reference_date: date | None,
        exercise_id: int | None,
        user_created_at: date,
    ) -> ReportSummary:
        today = date.today()
        ref = reference_date or today

        if period == ReportPeriod.day:
            start, end = ref, ref
        elif period == ReportPeriod.week:
            start = ref - timedelta(days=ref.weekday())  # 월요일
            end = start + timedelta(days=6)
        elif period == ReportPeriod.month:
            start = ref.replace(day=1)
            next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
            end = next_month - timedelta(days=1)
        else:  # cumulative
            start, end = user_created_at, today

        rows = await self.repo.get_summary(user_id, start, end, exercise_id)

        total_sessions = sum(int(r.sessions_count) for r in rows)
        total_duration = sum(int(r.total_duration_sec) for r in rows)

        # 전체 avg_score: 세션 수 가중 평균
        weighted_sum = sum(
            float(r.avg_score) * int(r.sessions_count)
            for r in rows
            if r.avg_score is not None
        )
        scored_sessions = sum(int(r.sessions_count) for r in rows if r.avg_score is not None)
        avg_score = Decimal(str(round(weighted_sum / scored_sessions, 2))) if scored_sessions else None

        # best_exercise: best_score 최고 종목
        best_row = max(
            (r for r in rows if r.best_score is not None),
            key=lambda r: r.best_score,
            default=None,
        )
        best_exercise = (
            BestExercise(id=best_row.exercise_id, name_ko=best_row.name_ko, best_score=best_row.best_score)
            if best_row
            else None
        )

        return ReportSummary(
            period=period,
            period_start=start,
            period_end=end,
            sessions_count=total_sessions,
            total_duration_sec=total_duration,
            avg_score=avg_score,
            best_exercise=best_exercise,
        )

    async def get_score_trend(
        self,
        user_id: int,
        days: int,
        exercise_id: int | None,
    ) -> ScoreTrendResponse:
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        rows = await self.repo.get_score_trend(user_id, start_date, today, exercise_id)

        # exercise_id별로 그룹핑
        series_map: dict[int, ScoreTrendSeries] = {}
        for row in rows:
            if row.exercise_id not in series_map:
                series_map[row.exercise_id] = ScoreTrendSeries(
                    exercise=EmbeddedExercise(id=row.exercise_id, name_ko=row.name_ko),
                    points=[],
                )
            series_map[row.exercise_id].points.append(
                ScoreTrendPoint(date=row.stat_date, avg_score=row.avg_score)
            )

        return ScoreTrendResponse(series=list(series_map.values()))

    async def get_evaluation(
        self,
        user_id: int,
        period: ReportPeriod,
        exercise_id: int | None,
        user_created_at: date,
    ) -> EvaluationResponse:
        summary = await self.get_summary(user_id, period, None, exercise_id, user_created_at)
        rows = await self.repo.get_summary(
            user_id,
            summary.period_start,
            summary.period_end,
            exercise_id,
        )

        # 1순위: LangGraph 기반 AI 종합 평가 (피드백 기록 + API 키가 있을 때)
        ai = await self._try_ai_evaluation(user_id, exercise_id, summary)
        if ai is not None:
            return EvaluationResponse(
                period=period,
                exercise_id=exercise_id,
                messages=ai["messages"],
                summary=ai["summary"],
                source=EvaluationSource.ai,
            )

        # 폴백: 규칙 기반 메시지
        messages = self._rule_based_messages(summary, len(rows))
        return EvaluationResponse(
            period=period,
            exercise_id=exercise_id,
            messages=messages,
            source=EvaluationSource.rule,
        )

    def _rule_based_messages(
        self, summary: ReportSummary, exercise_count: int
    ) -> list[EvaluationMessage]:
        """집계 통계만으로 만드는 규칙 기반 평가 메시지(AI 폴백용)."""
        messages: list[EvaluationMessage] = []
        pos = EvaluationMessageType.positive
        warn = EvaluationMessageType.warning
        tip = EvaluationMessageType.tip

        total = summary.sessions_count
        avg = float(summary.avg_score) if summary.avg_score is not None else None

        if total == 0:
            messages.append(EvaluationMessage(type=warn, text="아직 운동 기록이 없어요. 오늘 첫 운동을 시작해 보세요!"))
            return messages

        if total >= 15:
            messages.append(EvaluationMessage(type=pos, text=f"정말 꾸준해요! 기간 내 {total}회나 운동했어요."))
        elif total >= 7:
            messages.append(EvaluationMessage(type=pos, text=f"꾸준히 운동하고 있어요. 총 {total}회 기록이 쌓였어요."))
        else:
            messages.append(EvaluationMessage(type=tip, text=f"운동 횟수를 조금 더 늘려보세요. 현재 {total}회예요."))

        if avg is not None:
            if avg >= 85:
                messages.append(EvaluationMessage(type=pos, text=f"평균 점수 {avg:.1f}점! 자세가 매우 안정적이에요."))
            elif avg >= 70:
                messages.append(EvaluationMessage(type=tip, text=f"평균 점수 {avg:.1f}점이에요. 조금만 더 집중하면 90점도 가능해요."))
            else:
                messages.append(EvaluationMessage(type=warn, text=f"평균 점수가 {avg:.1f}점이에요. 기본 자세를 다시 점검해 보세요."))

        if summary.best_exercise:
            best = summary.best_exercise
            messages.append(EvaluationMessage(type=pos, text=f"가장 잘하는 종목은 {best.name_ko}이에요. 최고 점수 {float(best.best_score):.1f}점!"))

        if exercise_count >= 3:
            messages.append(EvaluationMessage(type=tip, text="다양한 종목을 골고루 운동하고 있어요. 균형 잡힌 루틴이에요!"))
        elif exercise_count == 1 and total >= 5:
            messages.append(EvaluationMessage(type=tip, text="한 종목에 집중하고 있어요. 다른 종목도 함께 도전해 보세요."))

        return messages

    async def _try_ai_evaluation(
        self,
        user_id: int,
        exercise_id: int | None,
        summary: ReportSummary,
    ) -> dict | None:
        """
        LangGraph long-term 그래프로 종합 평가를 시도한다.
        피드백이 없거나 / API 키가 없거나 / 실패하면 None → 규칙 기반으로 폴백.
        """
        if summary.sessions_count == 0:
            return None

        feedback_texts = await FeedbackRepository(self.db).list_recent_contents(
            user_id, exercise_id, limit=60
        )
        if not feedback_texts:
            return None

        stats = {
            "sessions_count": summary.sessions_count,
            "avg_score": float(summary.avg_score) if summary.avg_score is not None else None,
            "best_exercise": summary.best_exercise.name_ko if summary.best_exercise else None,
        }

        from app.config import settings

        api_key = settings.google_api_key or settings.gemini_api_key
        if not api_key:
            return None

        try:
            # langgraph/langchain 은 무거운 선택적 의존성 → lazy import.
            from ai.llm.report_long_term import run_long_term_evaluation

            result = await asyncio.wait_for(
                asyncio.to_thread(
                    run_long_term_evaluation,
                    feedback_texts,
                    stats,
                    api_key,
                    settings.gemini_model,
                ),
                timeout=_AI_EVALUATION_TIMEOUT_SEC,
            )
        except Exception as exc:  # noqa: BLE001 — 어떤 실패든 규칙 기반으로 폴백
            logger.warning("AI 종합 평가 실패, 규칙 기반으로 폴백: %s", exc)
            return None

        if not result:
            return None

        messages: list[EvaluationMessage] = []
        for item in result.get("messages", []):
            try:
                messages.append(
                    EvaluationMessage(
                        type=EvaluationMessageType(item["type"]),
                        text=item["text"],
                    )
                )
            except (KeyError, ValueError):
                continue

        if not messages:
            return None

        return {"messages": messages, "summary": result.get("summary", "")}

    async def get_overview(self, user_id: int, user_created_at: date) -> ReportOverview:
        """누적 요약 + 최근 30일 캘린더 + 최근 90일 점수 추이 + 종합 평가를 병렬로 조합."""
        summary, calendar, score_trend, evaluation = await asyncio.gather(
            self.get_summary(user_id, ReportPeriod.cumulative, None, None, user_created_at),
            self.get_calendar(user_id, 30),
            self.get_score_trend(user_id, 90, None),
            self.get_evaluation(user_id, ReportPeriod.cumulative, None, user_created_at),
        )
        return ReportOverview(summary=summary, calendar=calendar, score_trend=score_trend, evaluation=evaluation)
