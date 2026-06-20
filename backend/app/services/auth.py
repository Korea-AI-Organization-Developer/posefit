import logging

import httpx
from fastapi import HTTPException
from jose import JWTError

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.repositories.user import UserRepository
from app.schemas.auth import AuthRefreshResponse, AuthSocialCallbackResponse
from app.security import (
    REFRESH,
    access_token_expires_in,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.services.user import UserService

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

SUPPORTED_PROVIDERS = {"google"}


async def exchange_google_code(code: str, redirect_uri: str) -> dict:
    """authorization code → access token → userinfo(sub/email/name/picture).

    redirect_uri 는 프론트가 OAuth 에서 사용한 값과 동일해야 구글이 검증을 통과시킨다.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        token_res = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if not token_res.is_success:
            logger.error("Google token exchange 실패 | status=%s body=%s redirect_uri=%s", token_res.status_code, token_res.text, redirect_uri)
        token_res.raise_for_status()
        access_token = token_res.json()["access_token"]

        userinfo_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_res.raise_for_status()
        return userinfo_res.json()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def social_login(
        self, provider: str, code: str, redirect_uri: str
    ) -> AuthSocialCallbackResponse:
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")

        try:
            userinfo = await exchange_google_code(code, redirect_uri)
        except (httpx.HTTPError, KeyError) as exc:
            logger.error("Google OAuth 실패 | provider=%s redirect_uri=%s error=%s", provider, redirect_uri, exc)
            raise HTTPException(
                status_code=400, detail="구글 OAuth 코드 교환에 실패했습니다"
            ) from exc

        uid = userinfo["sub"]
        email = userinfo.get("email")
        name = userinfo.get("name") or "사용자"
        picture = userinfo.get("picture")

        user = await self.repo.find_by_social("google", uid)
        is_new_user = user is None

        if is_new_user:
            user = await self.repo.create_user(nickname=name)
            await self.repo.create_social_account(
                user.id, "google", uid, email, picture
            )
        else:
            # 로그인 시 프로필 사진·이메일 갱신 (openapi: 로그인 시 갱신)
            account = await self.repo.get_social_account("google", uid)
            if account is not None:
                account.provider_avatar_url = picture
                account.provider_email = email

        await self.db.commit()
        await self.db.refresh(user)  # token_version 등 server_default 반영

        user_read = await UserService(self.db).get_me(user.id)
        return AuthSocialCallbackResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id, user.token_version),
            access_token_expires_in=access_token_expires_in(),
            is_new_user=is_new_user,
            user=user_read,
        )

    async def refresh(self, refresh_token: str) -> AuthRefreshResponse:
        try:
            payload = decode_token(refresh_token, REFRESH)
            user_id = int(payload["sub"])
            ver = payload["ver"]
        except (JWTError, KeyError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다") from exc

        user = await self.repo.get_by_id(user_id)
        if user is None or user.token_version != ver:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

        return AuthRefreshResponse(
            access_token=create_access_token(user_id),
            access_token_expires_in=access_token_expires_in(),
        )

    async def logout(self, user) -> None:
        """token_version 을 올려 기존 refresh 토큰을 일괄 무효화한다."""
        user.token_version += 1
        await self.db.commit()
