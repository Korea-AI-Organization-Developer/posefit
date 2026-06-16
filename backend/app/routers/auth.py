from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthRefreshRequest,
    AuthRefreshResponse,
    AuthSocialCallbackRequest,
    AuthSocialCallbackResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/social/{provider}/callback", response_model=AuthSocialCallbackResponse)
async def social_callback(
    provider: str,
    body: AuthSocialCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """소셜 로그인 콜백 — 프론트가 받은 code 를 교환해 로그인/가입 처리."""
    return await AuthService(db).social_login(provider, body.code, body.redirect_uri)


@router.post("/refresh", response_model=AuthRefreshResponse)
async def refresh(body: AuthRefreshRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 refresh 토큰 일괄 무효화 (token_version +1)."""
    await AuthService(db).logout(user)
