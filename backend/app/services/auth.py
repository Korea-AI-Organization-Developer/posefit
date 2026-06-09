from datetime import datetime, timedelta, timezone

import httpx
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.repositories.user import UserRepository
from app.schemas.auth import SignupCompleteRequest

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def _make_token(payload: dict, expire_minutes: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    return jwt.encode({**payload, "exp": exp}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def make_access_token(user_id: int) -> str:
    return _make_token({"sub": str(user_id), "type": "access"}, settings.jwt_expire_minutes)


def make_temp_token(google_uid: str, email: str | None, name: str) -> str:
    return _make_token(
        {"sub": google_uid, "email": email, "name": name, "type": "temp"},
        settings.temp_token_expire_minutes,
    )


def decode_temp_token(token: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "temp":
        raise JWTError("invalid token type")
    return payload


def get_google_auth_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


async def exchange_google_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
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
        self.repo = UserRepository(db)
        self.db = db

    async def handle_google_callback(self, code: str):
        """
        구글 콜백 처리.
        - 기존 유저 → (user, None) 반환
        - 신규 유저 → (None, temp_token) 반환
        """
        userinfo = await exchange_google_code(code)
        google_uid = userinfo["sub"]
        email = userinfo.get("email")
        name = userinfo.get("name", "")

        user = await self.repo.find_by_social("google", google_uid)
        if user:
            return user, None

        temp_token = make_temp_token(google_uid, email, name)
        return None, temp_token

    async def complete_signup(self, req: SignupCompleteRequest):
        payload = decode_temp_token(req.temp_token)
        google_uid = payload["sub"]
        email = payload.get("email")

        # 중복 가입 방지
        existing = await self.repo.find_by_social("google", google_uid)
        if existing:
            return existing

        user = await self.repo.create_user(nickname=req.nickname)
        await self.repo.create_social_account(user.id, "google", google_uid, email)
        await self.repo.create_user_detail(
            user.id, req.birthdate, req.gender, req.height, req.weight
        )
        await self.repo.create_agreement(
            user.id, req.tos_agreed, req.privacy_agreed, req.biometric_agreed, req.marketing_agreed
        )
        await self.db.commit()
        await self.db.refresh(user)
        return user
