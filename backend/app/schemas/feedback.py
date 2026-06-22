# datetime: 피드백 생성 시각(created_at)의 타입.
from datetime import datetime

# FeedbackSeverity("info"|"warning"|"critical"), FeedbackSource("rule"|"llm"):
#   엉뚱한 문자열이 들어오지 못하도록 Enum으로 타입을 고정한다. models/enums.py 정의를 재사용.
from app.models.enums import FeedbackSeverity, FeedbackSource

# CamelModel: 내부는 snake_case, JSON 출력은 camelCase(openapi와 동일)로 변환해주는 공통 베이스.
from app.schemas.base import CamelModel


# FeedbackRead: 피드백 한 건의 응답 형식. docs/openapi.yaml 의 Feedback 스키마와 1:1.
#   generated_by → JSON 에서는 generatedBy, created_at → createdAt 로 자동 변환된다.
class FeedbackRead(CamelModel):
    id: int                          # 피드백 고유 번호 (feedbacks.id). 정렬 기준(id ASC)이기도 하다.
    severity: FeedbackSeverity       # 중요도: info / warning / critical.
    generated_by: FeedbackSource     # 생성 주체: rule(규칙 기반) / llm(생성형).
    content: str                     # 사용자에게 보여줄 자연어 피드백.
    created_at: datetime             # 생성 시각(UTC).


# ExerciseFeedbackSummaryRequest: 운동 종합 피드백 생성 요청 본문.
#   sessionIds = 이번 운동 묶음(bout)에서 진행한 세트 세션 id 들(= 각 STOP 대상 세션).
#   별도 저장 식별자(ERD 변경) 없이, 프런트가 들고 있는 세션 id 목록으로 "현재 묶음"을 정한다.
class ExerciseFeedbackSummaryRequest(CamelModel):
    session_ids: list[int]           # 최소 1개. 요청 사용자 소유 + 해당 종목의 세션이어야 한다.


# ExerciseFeedbackSummaryResponse: 여러 세트 피드백을 LLM 이 합쳐 만든 운동 종합 피드백 1건.
#   DB 에 저장하지 않으므로 id 가 없다(저장하려면 ERD 변경 필요 → 의도적으로 미저장).
class ExerciseFeedbackSummaryResponse(CamelModel):
    exercise_id: int                 # 어떤 종목에 대한 종합인지.
    set_count: int                   # 종합에 사용된 세트(피드백) 개수.
    generated_by: FeedbackSource     # 항상 llm.
    content: str                     # 운동 전체 코칭 코멘트.
    created_at: datetime             # 생성 시각(응답 시점). 저장하지 않으므로 표시용.
