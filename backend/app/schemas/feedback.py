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
