import asyncio
from datetime import datetime, time, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import FeedbackSource
from app.models.user import User
from app.repositories.exercise import ExerciseRepository
from app.repositories.feedback import FeedbackRepository
from app.repositories.workout_session import WorkoutSessionRepository
from app.schemas.feedback import ExerciseFeedbackSummaryResponse, FeedbackRead

KST = timezone(timedelta(hours=9))


def _today_kst_range_utc() -> tuple[datetime, datetime]:
    now_kst = datetime.now(KST)
    start_kst = datetime.combine(now_kst.date(), time.min, tzinfo=KST)
    end_kst = start_kst + timedelta(days=1)
    start_utc = start_kst.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_kst.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = FeedbackRepository(db)
        self.exercise_repo = ExerciseRepository(db)
        self.session_repo = WorkoutSessionRepository(db)

    async def list_today(
        self, user: User, exercise_id: int
    ) -> list[FeedbackRead] | None:
        exercise = await self.exercise_repo.get_by_id(exercise_id)
        if exercise is None:
            return None

        start_utc, end_utc = _today_kst_range_utc()
        rows = await self.repo.list_today(user.id, exercise_id, start_utc, end_utc)
        return [FeedbackRead.model_validate(row) for row in rows]

    async def summarize(
        self, user: User, exercise_id: int, session_ids: list[int]
    ) -> ExerciseFeedbackSummaryResponse | None:
        exercise = await self.exercise_repo.get_by_id(exercise_id)
        if exercise is None:
            return None

        rows = await self.repo.list_by_sessions(user.id, exercise_id, session_ids)
        if not rows:
            raise HTTPException(
                status_code=422, detail="합칠 세트 피드백이 없습니다."
            )

        scores = await self.session_repo.get_scores_by_ids(
            [row.session_id for row in rows]
        )

        today_set_results = [
            {
                "set_number": i + 1,
                "session_id": row.session_id,
                "content":    row.content,
                "score":      scores.get(row.session_id),
            }
            for i, row in enumerate(rows)
        ]

        from ai.llm.langgraph_V2 import posefit_graph

        result: dict = dict(
            await asyncio.to_thread(
                posefit_graph.invoke,
                {"exercise": exercise.name_ko, "today_set_results": today_set_results},
            )
        )

        final = result.get("final_feedback") or {}
        feedback_text = final.get("feedback_text") or {}
        content = (
            feedback_text.get("coaching")
            or feedback_text.get("summary")
            or ""
        )
        avg_score = (result.get("daily_feedback") or {}).get("avg_score")

        # 마지막 session_id에 일일 종합 피드백 1건으로 저장
        saved = await self.repo.create(
            session_id=rows[-1].session_id,
            content=content,
            generated_by=FeedbackSource.llm,
        )
        await self.db.commit()
        await self.db.refresh(saved)

        return ExerciseFeedbackSummaryResponse(
            exercise_id=exercise_id,
            set_count=len(rows),
            generated_by=FeedbackSource.llm.value,
            content=content,
            avg_score=float(avg_score) if avg_score is not None else None,
            created_at=saved.created_at,
        )
