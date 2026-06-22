from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminAuditLog


class AdminAuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, page: int, size: int) -> tuple[list[AdminAuditLog], int]:
        total_result = await self.db.execute(
            select(func.count()).select_from(AdminAuditLog)
        )
        total = total_result.scalar_one()

        rows = await self.db.execute(
            select(AdminAuditLog)
            .order_by(AdminAuditLog.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(rows.scalars().all()), total
