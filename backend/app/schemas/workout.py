from app.schemas.base import CamelModel
from app.schemas.feedback import FeedbackRead


class FaceGateStatusResponse(CamelModel):
    """운동 진입 전 얼굴 게이트 초기 모드 응답."""
    mode: str   # "registration" | "verification"


class StopSessionResponse(CamelModel):
    """POST /workout-sessions:stop 응답 — 세트 1회 결과.

    session_id/video_url 은 프런트가 이번 묶음(bout)의 세션 추적·영상 저장에 쓰고,
    feedback 은 그 세트의 저장된 LLM 피드백(=하단 세트 카드 표시용)이다.
    """
    session_id: int
    video_url: str
    score: float | None = None
    feedback: FeedbackRead


class SaveSessionResponse(CamelModel):
    """POST /workout-sessions/{id}:save, :discard 응답."""
    success: bool


class NextSessionResponse(CamelModel):
    """POST /workout-sessions/{id}:next 응답 — 새 세션 리다이렉트용 최소 정보."""
    id: int
    exercise_id: int
    status: str


class SaveSessionResponse(CamelModel):
    """POST /workout-sessions/{id}:save, :discard 응답."""
    success: bool


class NextSessionResponse(CamelModel):
    """POST /workout-sessions/{id}:next 응답 — 새 세션 리다이렉트용 최소 정보."""
    id: int
    exercise_id: int
    status: str
