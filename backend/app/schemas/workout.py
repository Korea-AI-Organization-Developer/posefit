from app.schemas.base import CamelModel


class FaceGateStatusResponse(CamelModel):
    """운동 진입 전 얼굴 게이트 초기 모드 응답."""
    mode: str   # "registration" | "verification"
