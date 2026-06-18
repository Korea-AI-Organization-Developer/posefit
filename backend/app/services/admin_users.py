from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserStatus
from app.repositories.admin_users import AdminUsersRepository
from app.schemas.admin_users import AdminUserDetail, AdminUserListItem, AdminUserPage, AdminUserUpdateRequest


class AdminUsersService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminUsersRepository(db)

    async def list_users(
        self,
        query: str | None,
        status: UserStatus | None,
        page: int,
        size: int,
    ) -> AdminUserPage:
        rows, total = await self.repo.list_users(query, status, page, size)
        items = [
            AdminUserListItem(
                id=user.id,
                nickname=user.nickname,
                email=email,
                role=user.role,
                status=user.status,
                created_at=user.created_at,
            )
            for user, email in rows
        ]
        return AdminUserPage(total=total, page=page, size=size, items=items)

    async def get_user_detail(self, user_id: int) -> AdminUserDetail:
        result = await self.repo.get_user_detail(user_id)
        if result is None:
            raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다")

        user, email, session_count = result
        detail = user.detail

        return AdminUserDetail(
            id=user.id,
            nickname=user.nickname,
            email=email,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            withdrawn_at=user.withdrawn_at,
            birthdate=detail.birthdate if detail else None,
            gender=detail.gender if detail else None,
            height=float(detail.height) if detail and detail.height is not None else None,
            weight=float(detail.weight) if detail and detail.weight is not None else None,
            face_registered=user.face_embedding is not None,
            marketing_agreed=user.agreement.marketing_agreed if user.agreement else None,
            session_count=session_count,
        )

    async def update_user_status(
        self,
        user_id: int,
        body: AdminUserUpdateRequest,
        admin_id: int,
        ip_address: str | None,
    ) -> AdminUserDetail:
        user = await self.repo.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다")

        prev_status = user.status
        user.status = body.status
        if body.status == UserStatus.withdrawn:
            user.withdrawn_at = datetime.now(timezone.utc)
        elif prev_status == UserStatus.withdrawn:
            user.withdrawn_at = None

        await self.repo.create_audit_log(
            admin_id=admin_id,
            action="update_user_status",
            target_type="user",
            target_id=str(user_id),
            detail={"from": prev_status.value, "to": body.status.value},
            ip_address=ip_address,
        )

        await self.db.commit()
        return await self.get_user_detail(user_id)
