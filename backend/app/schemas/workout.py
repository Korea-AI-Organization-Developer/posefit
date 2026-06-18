from app.schemas.base import CamelModel


class FaceGateStatusResponse(CamelModel):
    """운동 진입 전 얼굴 게이트 초기 모드 응답."""
    mode: str   # "registration" | "verification"


class StopSessionResponse(CamelModel):
    """POST /workout-sessions:stop 응답 — 저장된 영상 URL + LLM 코멘트."""
    video_url: str
    comment: str
    score: float | None = None
