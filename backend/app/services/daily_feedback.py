# AsyncSession: DB 세션. router 에서 받아 repository 로 넘긴다.
from sqlalchemy.ext.asyncio import AsyncSession

# User: 로그인 사용자. user.id 로 "본인 세션의 피드백"만 종합한다.
from app.models.user import User
# ExerciseRepository: 종목 존재 확인(없으면 404) + 그래프에 넘길 종목명(name_ko) 조회.
from app.repositories.exercise import ExerciseRepository
# FeedbackRepository: 오늘(KST) 세트 피드백 조회. GET /feedbacks 와 같은 쿼리를 재사용한다.
from app.repositories.feedback import FeedbackRepository
# DailyFeedbackRead: 응답 형식.
from app.schemas.daily_feedback import DailyFeedbackRead
# _today_kst_range_utc: "오늘(KST)"의 [start, end) UTC 경계. GET /feedbacks 와 동일한 기준을
#   써야 두 엔드포인트가 같은 피드백 집합을 보므로, 정의를 복제하지 않고 그대로 재사용한다(일관성).
from app.services.feedback import _today_kst_range_utc


# DailyFeedbackService: 오늘 세트 피드백들을 LangGraph 일일 분기로 종합하는 로직 층.
#   "API 가 노출하는 오늘 피드백" 과 "그래프가 평가하는 입력" 을 같은 쿼리로 묶어
#   두 결과가 어긋나지 않게(consistent) 한다.
class DailyFeedbackService:
    def __init__(self, db: AsyncSession):
        self.feedback_repo = FeedbackRepository(db)
        self.exercise_repo = ExerciseRepository(db)

    # summarize_today: 지정 종목의 오늘(KST) 세트 피드백을 모아 일일 종합 피드백을 만든다.
    #   종목이 없으면 None(라우터가 404 로 변환). 오늘 피드백이 0건이면 빈 종합을 반환한다.
    async def summarize_today(
        self, user: User, exercise_id: int
    ) -> DailyFeedbackRead | None:
        exercise = await self.exercise_repo.get_by_id(exercise_id)
        if exercise is None:
            return None

        # GET /exercises/{id}/feedbacks 와 동일한 사용자·종목·오늘(KST) 조건으로 조회.
        start_utc, end_utc = _today_kst_range_utc()
        rows = await self.feedback_repo.list_today(
            user.id, exercise_id, start_utc, end_utc
        )

        # ORM 피드백 → 그래프 입력(today_feedbacks) 형태로 변환.
        #   langgraph_V1._normalize_feedback_item 이 읽는 키에 맞춘다.
        #   created_at 은 그래프 정렬 키이므로 ISO 문자열로 넘긴다.
        today_feedbacks = [
            {
                "id": row.id,
                "session_id": row.session_id,
                "severity": row.severity.value,
                "generated_by": row.generated_by.value,
                "content": row.content,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]

        # 그래프는 무겁고 LLM 의존성이 있어, 앱 부팅 부담을 줄이려 함수 안에서 지연 import 한다
        # (ai.face 모듈을 함수 내부에서 import 하는 기존 패턴과 동일).
        from ai.llm.langgraph_V1 import posefit_graph

        state = await posefit_graph.ainvoke(
            {
                "exercise": exercise.name_ko,
                "today_feedbacks": today_feedbacks,
            }
        )

        final = state.get("final_feedback", {})
        feedback_text = final.get("feedback_text", {})
        return DailyFeedbackRead(
            severity=final.get("severity", "info"),
            generated_by=final.get("generated_by", "llm"),
            content=final.get("content", ""),
            feedback_count=final.get("feedback_count", 0),
            source_feedback_ids=final.get("source_feedback_ids", []),
            summary=feedback_text.get("summary", ""),
            main_issue=feedback_text.get("main_issue", ""),
            coaching=feedback_text.get("coaching", ""),
            next_action=feedback_text.get("next_action", ""),
        )
