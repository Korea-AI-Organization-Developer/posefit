# datetime: "오늘(KST)" 범위를 UTC 경계값으로 받아 created_at 과 비교하는 데 쓴다.
from datetime import datetime

# select: 조회문(SELECT ...)을 파이썬으로 만드는 도구.
from sqlalchemy import select

# AsyncSession: DB 비동기 연결(세션) 타입.
from sqlalchemy.ext.asyncio import AsyncSession

# Feedback: feedbacks 테이블 모델. WorkoutSession: 소유자(user)·종목(exercise) 필터를 위해 조인한다.
from app.models.workout import Feedback, WorkoutSession


# FeedbackRepository: 피드백을 DB에서 꺼내오는 일만 담당(commit 하지 않는다).
class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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
