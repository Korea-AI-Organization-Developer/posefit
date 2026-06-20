"""공통 FastAPI 의존성 — Bearer 액세스 토큰으로 현재 사용자/관리자 식별."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin import AdminAccount
from app.models.enums import AdminStatus, UserStatus
from app.models.user import User
from app.repositories.admin_auth import AdminAuthRepository
from app.repositories.user import UserRepository
from app.security import ACCESS, ADMIN_ACCESS, decode_token

bearer_scheme = HTTPBearer(auto_error=True)
admin_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials, ACCESS)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="인증이 필요합니다") from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or user.status != UserStatus.active:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    return user


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(admin_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AdminAccount:
    try:
        payload = decode_token(credentials.credentials, ADMIN_ACCESS)
        admin_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="인증이 필요합니다") from exc

    admin = await AdminAuthRepository(db).get_by_id(admin_id)
    if admin is None or admin.status != AdminStatus.active:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    return admin
