from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.admin import AdminAccount
from app.models.enums import UserStatus
from app.schemas.admin_users import AdminUserDetail, AdminUserPage, AdminUserUpdateRequest
from app.services.admin_users import AdminUsersService

router = APIRouter(prefix="/admin", tags=["Admin Users"])


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_admin_user(
    user_id: int,
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminUsersService(db).get_user_detail(user_id)


@router.patch("/users/{user_id}", response_model=AdminUserDetail)
async def update_admin_user_status(
    user_id: int,
    body: AdminUserUpdateRequest,
    request: Request,
    admin: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await AdminUsersService(db).update_user_status(user_id, body, admin.id, ip)


@router.get("/users", response_model=AdminUserPage)
async def list_admin_users(
    query: str | None = Query(default=None, description="닉네임 또는 이메일 부분 일치"),
    status: UserStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminUsersService(db).list_users(query, status, page, size)
