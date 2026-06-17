"""운동 진입 얼굴 게이트 API.

흐름:
    1. GET /workout/face-gate/status  → 얼굴 등록 여부 확인 (초기 모드 반환)
    2. WS  /workout/face-gate/ws      → 프레임 스트리밍으로 등록·인증 처리

WebSocket 프로토콜:
    Client → Server : JPEG 프레임 (binary)
    Server → Client : JSON  { mode, message, progress, total, faceInGuide }

    mode 값:
        "registration" — 얼굴 등록 진행 중
        "verification" — 얼굴 인증 진행 중
        "passed"       — 인증 통과 → 운동 화면 진입
        "failed"       — 연결 종료 (재시도 필요)
"""

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from ai.workout.face_gate import GateMode, WorkoutFaceGate
from app.database import get_db
from app.dependencies import get_current_user
from app.models.enums import UserStatus
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.workout import FaceGateStatusResponse
from app.security import ACCESS, decode_token

router = APIRouter(prefix="/workout", tags=["Workout"])


@router.get("/face-gate/status", response_model=FaceGateStatusResponse)
async def face_gate_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    운동 시작 시 얼굴 게이트 초기 모드를 반환한다.

    - 얼굴 미등록 → mode: "registration"
    - 얼굴 등록됨 → mode: "verification"

    프론트엔드는 이 값을 보고 WebSocket 연결 후 UI 초기 화면을 결정한다.
    """
    gate = WorkoutFaceGate(user.id)
    mode = await gate.initialize(db)
    return FaceGateStatusResponse(mode=mode.value)


@router.websocket("/face-gate/ws")
async def face_gate_ws(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token (Bearer 헤더 대체)"),
    reregister: bool = Query(False, description="True 이면 DB 임베딩 무시하고 등록 모드 강제"),
    db: AsyncSession = Depends(get_db),
):
    """
    얼굴 등록·인증 WebSocket 엔드포인트.

    연결 방법: ws://host/api/v1/workout/face-gate/ws?token=<access_token>

    알고리즘 루프:
        REGISTRATION 모드
            └ 가이드 박스 안에 얼굴이 감지될 때마다 샘플 캡쳐
            └ samples_needed 장 수집 완료 → 인코딩·DB 저장
            └ 자동으로 VERIFICATION 모드로 전환
        VERIFICATION 모드
            └ 저장된 임베딩과 현재 프레임 비교
            └ verify_streak_needed 연속 성공 → mode: "passed" 전송 후 종료
            └ verify_fail_limit 연속 실패 → mode: "registration" 으로 재전환 (재캡쳐)
    """
    # ── 토큰 검증 (WebSocket 은 Authorization 헤더 미지원) ──────────
    try:
        payload = decode_token(token, ACCESS)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        await websocket.close(code=4001, reason="인증 실패")
        return

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or user.status != UserStatus.active:
        await websocket.close(code=4001, reason="인증 실패")
        return

    await websocket.accept()

    gate = WorkoutFaceGate(user_id)
    mode = await gate.initialize(db, force_registration=reregister)

    # 초기 상태 전송
    await websocket.send_json({
        "mode":     mode.value,
        "message":  "준비되었습니다",
        "progress": 0,
        "total": (
            gate.samples_needed if mode == GateMode.REGISTRATION
            else gate.verify_streak_needed
        ),
    })

    try:
        while gate.mode not in (GateMode.PASSED, GateMode.FAILED):
            frame_bytes = await websocket.receive_bytes()
            result = await gate.process_frame(frame_bytes, db)

            await websocket.send_json({
                "mode":        result.mode.value,
                "message":     result.message,
                "progress":    result.progress,
                "total":       result.total,
                "faceInGuide": result.face_in_guide,
            })

            if result.mode == GateMode.PASSED:
                break
    except WebSocketDisconnect:
        pass
