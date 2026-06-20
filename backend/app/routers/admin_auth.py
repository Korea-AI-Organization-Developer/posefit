from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.admin import AdminAccount
from app.schemas.admin_auth import (
    AdminLoginRequest,
    AdminRead,
    AdminRefreshRequest,
    AdminRefreshResponse,
    AdminTokenResponse,
)
from app.services.admin_auth import AdminAuthService

router = APIRouter(prefix="/admin", tags=["Admin Auth"])


@router.post("/auth/login", response_model=AdminTokenResponse)
async def admin_login(
    body: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AdminAuthService(db).login(body)


@router.post("/auth/refresh", response_model=AdminRefreshResponse)
async def admin_refresh(
    body: AdminRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AdminAuthService(db).refresh(body)


@router.post("/auth/logout", status_code=204)
async def admin_logout(
    admin: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await AdminAuthService(db).logout(admin)
    return Response(status_code=204)


@router.get("/me", response_model=AdminRead)
async def admin_me(
    admin: AdminAccount = Depends(get_current_admin),
):
    return AdminRead.model_validate(admin)
