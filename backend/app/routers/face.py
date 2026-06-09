from fastapi import APIRouter, Depends, HTTPException, Header
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.face import FaceLoginRequest, FaceLoginResponse, FaceRegisterRequest
from app.services.auth import make_access_token
from app.services.face import FaceService

router = APIRouter(prefix="/face", tags=["face"])


def _get_user_id(authorization: str) -> int:
    try:
        scheme, token = authorization.split()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="인증이 필요합니다")


@router.post("/register", status_code=204)
async def register_face(
    req: FaceRegisterRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """로그인된 사용자의 얼굴을 등록."""
    user_id = _get_user_id(authorization)
    try:
        await FaceService(db).register(user_id, req.image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"얼굴 감지 실패: {str(e)}")


@router.post("/login", response_model=FaceLoginResponse)
async def face_login(
    req: FaceLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """얼굴로 로그인. 일치하는 유저가 있으면 JWT 발급."""
    try:
        user = await FaceService(db).identify(req.image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"얼굴 인식 오류: {str(e)}")

    if not user:
        raise HTTPException(status_code=401, detail="일치하는 얼굴을 찾을 수 없습니다")

    token = make_access_token(user.id)
    return FaceLoginResponse(access_token=token, nickname=user.nickname)
