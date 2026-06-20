from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminAccount


class AdminAuthRepository:
    """DB 접근만 담당 — commit 하지 않는다(트랜잭션은 service)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> AdminAccount | None:
        result = await self.db.execute(
            select(AdminAccount).where(AdminAccount.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, admin_id: int) -> AdminAccount | None:
        result = await self.db.execute(
            select(AdminAccount).where(AdminAccount.id == admin_id)
        )
        return result.scalar_one_or_none()
