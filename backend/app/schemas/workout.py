from app.schemas.base import CamelModel


class FaceGateStatusResponse(CamelModel):
    """운동 진입 전 얼굴 게이트 초기 모드 응답."""
    mode: str   # "registration" | "verification"


class StopSessionResponse(CamelModel):
    """POST /workout-sessions:stop 응답 — 세션 ID + 저장된 영상 URL + LLM 코멘트."""
    session_id: int
    video_url: str
    comment: str
    score: float | None = None


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
