# FeedbackSeverity("info"|"warning"|"critical"), FeedbackSource("rule"|"llm"):
#   세트 피드백(FeedbackRead)과 동일한 Enum 을 재사용해 일일 종합 피드백의 타입을 맞춘다.
from app.models.enums import FeedbackSeverity, FeedbackSource
# CamelModel: 내부 snake_case ↔ JSON camelCase 변환 공통 베이스(FeedbackRead 와 동일).
from app.schemas.base import CamelModel


# DailyFeedbackRead: 오늘(KST) 세트 피드백들을 LangGraph 일일 분기로 종합한 결과의 응답 형식.
#   - severity/generated_by/content 는 세트 피드백(FeedbackRead)과 같은 의미·타입이라
#     프론트가 단일 피드백과 동일하게 다룰 수 있다(일관성).
#   - 나머지 필드는 "여러 세트를 묶어 평가"하면서 생기는 종합 메타데이터.
class DailyFeedbackRead(CamelModel):
    severity: FeedbackSeverity        # 오늘 피드백 중 가장 높은 중요도.
    generated_by: FeedbackSource      # 생성 주체: rule / llm.
    content: str                      # 화면 출력용 한 줄 종합 피드백.
    feedback_count: int               # 종합에 사용된 오늘 세트 피드백 개수.
    source_feedback_ids: list[int]    # 종합 근거가 된 feedbacks.id 목록.
    summary: str                      # 요약.
    main_issue: str                   # 핵심 교정 포인트.
    coaching: str                     # 코칭 메시지.
    next_action: str                  # 다음 세트 권장 행동.
