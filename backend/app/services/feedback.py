# datetime/time/timedelta/timezone: "오늘(KST)" 범위를 계산해 UTC 경계로 바꾸는 데 쓴다.
from datetime import datetime, time, timedelta, timezone

# HTTPException: 종합 피드백 입력이 비어 있을 때 422 로 알리는 데 쓴다.
from fastapi import HTTPException
# AsyncSession: DB 세션. router 에서 받아 repository 로 넘긴다.
from sqlalchemy.ext.asyncio import AsyncSession

# FeedbackSource: 종합 피드백 생성 주체(llm) 표기.
from app.models.enums import FeedbackSource
# User: 로그인 사용자. user.id 로 "본인 세션의 피드백"만 조회한다.
from app.models.user import User
# ExerciseRepository: 종목 존재 여부 확인용(없으면 404). FeedbackRepository: 실제 피드백 조회.
from app.repositories.exercise import ExerciseRepository
from app.repositories.feedback import FeedbackRepository
# FeedbackRead / 종합 응답: 응답 형식. ORM 객체를 이 모양으로 변환해 반환한다.
from app.schemas.feedback import ExerciseFeedbackSummaryResponse, FeedbackRead

# KST: 한국 표준시(UTC+9). DB 는 UTC 로 저장하므로, "오늘"의 기준은 KST 로 잡고 UTC 로 변환해 비교한다.
KST = timezone(timedelta(hours=9))


# combine_feedbacks_llm: 여러 세트 피드백을 하나의 운동 종합 코멘트로 합친다.
#   ⚠ 실제 RAG/LLM 연동은 추후 구현. 현재는 입력을 이어붙인 자리표시(placeholder) 문자열을 돌려준다.
async def combine_feedbacks_llm(contents: list[str]) -> str:
    joined = " / ".join(contents)
    return f"[종합 피드백 자리표시] 총 {len(contents)}세트: {joined}"


# _today_kst_range_utc: 지금 시각 기준 "오늘(KST)"의 [시작, 끝) 을 UTC naive datetime 으로 돌려준다.
#   예) KST 2026-06-18 자정~다음날 자정 → UTC 2026-06-17 15:00 ~ 2026-06-18 15:00.
#   DB 의 created_at 은 tz 정보 없는 UTC 이므로, 비교 대상도 tzinfo 를 떼어(naive UTC) 맞춘다.
def _today_kst_range_utc() -> tuple[datetime, datetime]:
    now_kst = datetime.now(KST)
    start_kst = datetime.combine(now_kst.date(), time.min, tzinfo=KST)  # 오늘 00:00 (KST)
    end_kst = start_kst + timedelta(days=1)                            # 내일 00:00 (KST)
    start_utc = start_kst.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_kst.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


# FeedbackService: "무엇을 할지" 결정하는 로직 층.
class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.repo = FeedbackRepository(db)
        self.exercise_repo = ExerciseRepository(db)

    # list_today: 지정 종목의 오늘(KST) 피드백 목록을 응답 형식으로 반환.
    #   종목이 존재하지 않으면 None 을 돌려준다(라우터가 404 로 변환).
    #   운동 중 날짜가 바뀌는 경우는 고려하지 않고 "오늘" 조건만 적용한다(스펙).
    async def list_today(
        self, user: User, exercise_id: int
    ) -> list[FeedbackRead] | None:
        exercise = await self.exercise_repo.get_by_id(exercise_id)
        if exercise is None:
            return None

        start_utc, end_utc = _today_kst_range_utc()
        rows = await self.repo.list_today(user.id, exercise_id, start_utc, end_utc)
        return [FeedbackRead.model_validate(row) for row in rows]

    # summarize: 이번 묶음(session_ids)의 세트 피드백을 모아 LLM 으로 운동 종합 피드백 1건을 만든다.
    #   - 종목이 없으면 None (라우터가 404).
    #   - session_ids 가 본인·해당 종목 소유가 아니면 자연히 걸러진다. 합칠 피드백이 하나도 없으면 422.
    #   - 결과는 저장하지 않고 반환만 한다(저장하려면 ERD 변경 필요).
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

        content = await combine_feedbacks_llm([row.content for row in rows])
        return ExerciseFeedbackSummaryResponse(
            exercise_id=exercise_id,
            set_count=len(rows),
            generated_by=FeedbackSource.llm,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
