import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.auth import SignupCompleteRequest, TokenResponse, UserMeResponse
from app.services.auth import AuthService, get_google_auth_url, make_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google")
async def google_login(source: str = "login"):
    state = f"{source}:{secrets.token_urlsafe(16)}"
    url = get_google_auth_url(state)
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(default="login:"),
    db: AsyncSession = Depends(get_db),
):
    # state에서 source 추출 (예: "signup:abc123" → "signup")
    source = state.split(":")[0] if ":" in state else "login"

    try:
        user, temp_token = await AuthService(db).handle_google_callback(code)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[OAuth 오류] {e}")
        return RedirectResponse(f"{settings.frontend_url}/login?error=oauth_failed")

    if user:
        token = make_access_token(user.id)
        if source == "signup":
            # 회원가입 시도했는데 이미 가입된 회원
            return RedirectResponse(f"{settings.frontend_url}/signup/already-member?token={token}")
        # 로그인 → 대시보드로
        return RedirectResponse(f"{settings.frontend_url}/?token={token}")

    # 신규 유저 → 임시 토큰과 함께 회원가입 2단계로
    return RedirectResponse(f"{settings.frontend_url}/signup?temp_token={temp_token}")


@router.post("/signup/complete", response_model=TokenResponse)
async def signup_complete(
    req: SignupCompleteRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await AuthService(db).complete_signup(req)
    except JWTError:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 토큰입니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    token = make_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    from jose import jwt
    from app.repositories.user import UserRepository

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user
