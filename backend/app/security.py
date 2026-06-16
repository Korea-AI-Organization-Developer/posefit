"""JWT 토큰 인코딩/디코딩 (DB 비의존 순수 함수).

토큰 종류:
- access : 15분. stateless — 매 요청 DB 조회 없이 검증.
- refresh: 14일. payload 의 `ver` 가 users.token_version 과 일치할 때만 유효.
            로그아웃 시 token_version 을 +1 하면 기존 refresh 토큰이 일괄 무효화된다.
"""

from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings

ACCESS = "access"
REFRESH = "refresh"


def _encode(payload: dict, expires: timedelta) -> str:
    exp = datetime.now(timezone.utc) + expires
    return jwt.encode(
        {**payload, "exp": exp},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(user_id: int) -> str:
    return _encode(
        {"sub": str(user_id), "type": ACCESS},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: int, token_version: int) -> str:
    return _encode(
        {"sub": str(user_id), "type": REFRESH, "ver": token_version},
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str) -> dict:
    """서명·만료를 검증하고 type 이 기대값과 다르면 JWTError 를 던진다."""
    from jose import JWTError

    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != expected_type:
        raise JWTError("unexpected token type")
    return payload


def access_token_expires_in() -> int:
    """accessToken 만료까지 초 (openapi accessTokenExpiresIn)."""
    return settings.access_token_expire_minutes * 60
