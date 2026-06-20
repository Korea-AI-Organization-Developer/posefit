from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.report import ReportRepository
import asyncio

from app.schemas.report import (
    BestExercise,
    CalendarDay,
    CalendarResponse,
    EmbeddedExercise,
    EvaluationMessage,
    EvaluationMessageType,
    EvaluationResponse,
    ReportOverview,
    ReportPeriod,
    ReportSummary,
    ScoreTrendPoint,
    ScoreTrendResponse,
    ScoreTrendSeries,
)


class ReportService:
    def __init__(self, db: AsyncSession):
        self.repo = ReportRepository(db)

    async def get_calendar(self, user_id: int, days: int) -> CalendarResponse:
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        rows = await self.repo.get_calendar(user_id, start_date, today)
        stat_map = {row.stat_date: row for row in rows}

        day_list = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            row = stat_map.get(d)
            day_list.append(
                CalendarDay(
                    date=d,
                    sessions_count=int(row.sessions_count) if row else 0,
                    avg_score=row.avg_score if row else None,
                )
            )
        return CalendarResponse(days=day_list)

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
        messages: list[EvaluationMessage] = []
        pos = EvaluationMessageType.positive
        warn = EvaluationMessageType.warning
        tip = EvaluationMessageType.tip

        total = summary.sessions_count
        avg = float(summary.avg_score) if summary.avg_score is not None else None
        exercise_count = len(rows)

        if total == 0:
            messages.append(EvaluationMessage(type=warn, text="아직 운동 기록이 없어요. 오늘 첫 운동을 시작해 보세요!"))
        else:
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

        return EvaluationResponse(period=period, exercise_id=exercise_id, messages=messages)

    async def get_overview(self, user_id: int, user_created_at: date) -> ReportOverview:
        """누적 요약 + 최근 30일 캘린더 + 최근 90일 점수 추이 + 종합 평가를 병렬로 조합."""
        summary, calendar, score_trend, evaluation = await asyncio.gather(
            self.get_summary(user_id, ReportPeriod.cumulative, None, None, user_created_at),
            self.get_calendar(user_id, 30),
            self.get_score_trend(user_id, 90, None),
            self.get_evaluation(user_id, ReportPeriod.cumulative, None, user_created_at),
        )
        return ReportOverview(summary=summary, calendar=calendar, score_trend=score_trend, evaluation=evaluation)
