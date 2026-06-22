# datetime: "오늘(KST)" 범위를 UTC 경계값으로 받아 created_at 과 비교하는 데 쓴다.
from datetime import datetime

# select: 조회문(SELECT ...)을 파이썬으로 만드는 도구.
from sqlalchemy import select

# AsyncSession: DB 비동기 연결(세션) 타입.
from sqlalchemy.ext.asyncio import AsyncSession

# Feedback: feedbacks 테이블 모델. WorkoutSession: 소유자(user)·종목(exercise) 필터를 위해 조인한다.
# FeedbackSeverity / FeedbackSource: 세트 피드백 저장 시 기본값 타입.
from app.models.enums import FeedbackSeverity, FeedbackSource
from app.models.workout import Feedback, WorkoutSession


# FeedbackRepository: 피드백을 DB에서 꺼내오는 일만 담당(commit 하지 않는다).
class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # create: 세트(STOP) 1회의 피드백 1건을 추가한다(commit 은 service 에서).
    #   flush 까지만 해서 id 가 채워진 객체를 돌려준다.
    async def create(
        self,
        session_id: int,
        content: str,
        severity: FeedbackSeverity = FeedbackSeverity.info,
        generated_by: FeedbackSource = FeedbackSource.llm,
    ) -> Feedback:
        feedback = Feedback(
            session_id=session_id,
            content=content,
            severity=severity,
            generated_by=generated_by,
        )
        self.db.add(feedback)
        await self.db.flush()
        return feedback

    # list_by_sessions: 지정한 세트 세션 id 들의 피드백을 id ASC 로 조회한다(종합 피드백 입력용).
    #   user_id / exercise_id 를 함께 걸어, 본인 소유 + 해당 종목의 세션만 통과시킨다(소유권·종목 검증).
    #   요청 세션 중 조건에 안 맞는 것은 자연히 제외된다.
    async def list_by_sessions(
        self,
        user_id: int,
        exercise_id: int,
        session_ids: list[int],
    ) -> list[Feedback]:
        if not session_ids:
            return []
        stmt = (
            select(Feedback)
            .join(WorkoutSession, Feedback.session_id == WorkoutSession.id)
            .where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.exercise_id == exercise_id,
                Feedback.session_id.in_(session_ids),
            )
            .order_by(Feedback.id.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # list_today: 특정 사용자·종목의 "오늘(KST)" 피드백을 id ASC 로 조회한다.
    #   user_id     = 본인 세션의 피드백만 보도록 제한(소유권 검증)
    #   exercise_id = 지정한 운동 종목 필터
    #   start_utc / end_utc = 오늘(KST) 00:00~24:00 을 UTC 로 변환한 [start, end) 경계(서비스에서 계산)
    async def list_today(
        self,
        user_id: int,
        exercise_id: int,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[Feedback]:
        # feedbacks 를 workout_sessions 에 조인 → 그 세션이 "이 사용자"의 "이 종목"인 것만 남긴다.
        # created_at 이 [start_utc, end_utc) 안에 든 것만(=오늘 KST). end 는 미포함이라 자정 경계가 깔끔하다.
        stmt = (
            select(Feedback)
            .join(WorkoutSession, Feedback.session_id == WorkoutSession.id)
            .where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.exercise_id == exercise_id,
                Feedback.created_at >= start_utc,
                Feedback.created_at < end_utc,
            )
            .order_by(Feedback.id.asc())  # 표시 순서는 id 오름차순.
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # list_recent_contents: 특정 사용자의 누적 피드백 본문(content)을 최신순으로 조회한다.
    #   리포트 "종합 평가"에서 LangGraph long-term 평가의 입력으로 쓴다.
    #   exercise_id 가 주어지면 해당 종목으로 한정한다(없으면 전체 종목).
    async def list_recent_contents(
        self,
        user_id: int,
        exercise_id: int | None = None,
        limit: int = 60,
    ) -> list[str]:
        stmt = (
            select(Feedback.content)
            .join(WorkoutSession, Feedback.session_id == WorkoutSession.id)
            .where(WorkoutSession.user_id == user_id)
        )
        if exercise_id is not None:
            stmt = stmt.where(WorkoutSession.exercise_id == exercise_id)
        stmt = stmt.order_by(Feedback.id.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return [content for content in result.scalars().all() if content]
