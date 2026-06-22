from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AdminRole
from app.repositories.admin_audit import AdminAuditRepository
from app.schemas.admin_audit import AuditLogItem, AuditLogPage


class AdminAuditService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminAuditRepository(db)

    async def list_logs(self, admin_role: AdminRole, page: int, size: int) -> AuditLogPage:
        if admin_role != AdminRole.super_admin:
            raise HTTPException(status_code=403, detail="최고 관리자만 접근할 수 있습니다")

        logs, total = await self.repo.list(page, size)
        return AuditLogPage(
            total=total,
            page=page,
            size=size,
            items=[AuditLogItem.model_validate(log) for log in logs],
        )
