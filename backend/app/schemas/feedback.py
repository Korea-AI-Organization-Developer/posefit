# datetime: 피드백 생성 시각(created_at)의 타입.
from datetime import datetime

# FeedbackSeverity("info"|"warning"|"critical"), FeedbackSource("rule"|"llm"):
#   엉뚱한 문자열이 들어오지 못하도록 Enum으로 타입을 고정한다. models/enums.py 정의를 재사용.
from app.models.enums import FeedbackSeverity, FeedbackSource

# CamelModel: 내부는 snake_case, JSON 출력은 camelCase(openapi와 동일)로 변환해주는 공통 베이스.
from app.schemas.base import CamelModel


# FeedbackTimelineItem: 구간별 피드백 한 항목.
# LangGraph _timestamp_items_from_timeline_feedback 출력과 1:1 대응.
# 필드명은 프론트 FeedbackTimelineItem(types.ts)과 camelCase 기준으로 맞춤.
# TODO: 필드명 확정 전 임시명 — 프론트 types.ts 의 주석과 함께 변경할 것
class FeedbackTimelineItem(CamelModel):
    timestamp: str   # LangGraph: timestamp[].time — 구간 시각 레이블 (예: "0~4초")
    comment: str     # LangGraph: timestamp[].coaching — 구간 설명 텍스트
    is_good: bool    # LangGraph: timestamp[].pose — True=정상 구간, False=오류 구간 / JSON: isGood


# FeedbackRead: 피드백 한 건의 응답 형식. docs/openapi.yaml 의 Feedback 스키마와 1:1.
#   generated_by → JSON 에서는 generatedBy, created_at → createdAt 로 자동 변환된다.
class FeedbackRead(CamelModel):
    id: int                          # 피드백 고유 번호 (feedbacks.id). 정렬 기준(id ASC)이기도 하다.
    severity: FeedbackSeverity       # 중요도: info / warning / critical.
    generated_by: FeedbackSource     # 생성 주체: rule(규칙 기반) / llm(생성형).
    content: str                     # 사용자에게 보여줄 자연어 피드백.
    created_at: datetime             # 생성 시각(UTC).
    # LangGraph 추가 출력 — DB 미저장, :stop 응답에서만 포함. 없으면 None.
    # TODO: 필드명 확정 전 임시명 — 프론트 types.ts 의 주석과 함께 변경할 것
    summary: str | None = None                          # LangGraph: feedback_text.summary
    timeline: list[FeedbackTimelineItem] | None = None  # LangGraph: feedback_text.timestamp


# ExerciseFeedbackSummaryRequest: 운동 종합 피드백 생성 요청 본문.
#   sessionIds = 이번 운동 묶음(bout)에서 진행한 세트 세션 id 들(= 각 STOP 대상 세션).
#   별도 저장 식별자(ERD 변경) 없이, 프런트가 들고 있는 세션 id 목록으로 "현재 묶음"을 정한다.
class ExerciseFeedbackSummaryRequest(CamelModel):
    session_ids: list[int]           # 최소 1개. 요청 사용자 소유 + 해당 종목의 세션이어야 한다.


# ExerciseFeedbackSummaryResponse: 여러 세트 피드백을 LLM 이 합쳐 만든 운동 종합 피드백 1건.
#   마지막 session_id 에 묶어 feedbacks 테이블에 저장한다.
class ExerciseFeedbackSummaryResponse(CamelModel):
    exercise_id: int                 # 어떤 종목에 대한 종합인지.
    set_count: int                   # 종합에 사용된 세트(피드백) 개수.
    generated_by: FeedbackSource     # 항상 llm.
    content: str                     # 운동 전체 코칭 코멘트.
    avg_score: float | None          # 세트별 점수의 평균(0~100). 점수 없으면 None. JSON: avgScore
    created_at: datetime             # DB 저장 시각.
