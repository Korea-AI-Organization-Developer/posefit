from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.admin import AdminAccount
from app.schemas.admin_audit import AuditLogPage
from app.services.admin_audit import AdminAuditService

router = APIRouter(prefix="/admin", tags=["Admin Audit"])


@router.get("/audit-logs", response_model=AuditLogPage)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    admin: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminAuditService(db).list_logs(admin.role, page, size)
