from datetime import datetime

from app.models.mixins import KST

import bcrypt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminAccount
from app.models.enums import AdminStatus
from app.repositories.admin_auth import AdminAuthRepository
from app.schemas.admin_auth import (
    AdminLoginRequest,
    AdminRead,
    AdminRefreshRequest,
    AdminRefreshResponse,
    AdminTokenResponse,
)
from app.security import (
    ADMIN_REFRESH,
    access_token_expires_in,
    create_admin_access_token,
    create_admin_refresh_token,
    decode_token,
)


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


class AdminAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminAuthRepository(db)

    async def login(self, req: AdminLoginRequest) -> AdminTokenResponse:
        admin = await self.repo.get_by_email(req.email)
        if admin is None or not _verify_password(req.password, admin.password_hash):
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
        if admin.status != AdminStatus.active:
            raise HTTPException(status_code=401, detail="비활성화된 관리자 계정입니다")

        admin.last_login_at = datetime.now(KST)
        await self.db.commit()
        await self.db.refresh(admin)

        return AdminTokenResponse(
            access_token=create_admin_access_token(admin.id),
            refresh_token=create_admin_refresh_token(admin.id, admin.token_version),
            access_token_expires_in=access_token_expires_in(),
            admin=AdminRead.model_validate(admin),
        )

    async def refresh(self, req: AdminRefreshRequest) -> AdminRefreshResponse:
        from jose import JWTError

        try:
            payload = decode_token(req.refresh_token, ADMIN_REFRESH)
            admin_id = int(payload["sub"])
            ver = payload["ver"]
        except (JWTError, KeyError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다") from exc

        admin = await self.repo.get_by_id(admin_id)
        if admin is None or admin.token_version != ver or admin.status != AdminStatus.active:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

        return AdminRefreshResponse(
            access_token=create_admin_access_token(admin_id),
            access_token_expires_in=access_token_expires_in(),
        )

    async def logout(self, admin: AdminAccount) -> None:
        admin.token_version += 1
        await self.db.commit()
