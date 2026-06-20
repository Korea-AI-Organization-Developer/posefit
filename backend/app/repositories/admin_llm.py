from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminAuditLog, LlmModel


class AdminLlmRepository:
    """DB 접근만 담당 — commit 하지 않는다(트랜잭션은 service)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[LlmModel]:
        result = await self.db.execute(select(LlmModel).order_by(LlmModel.id))
        return list(result.scalars().all())

    async def create(
        self,
        provider: str,
        model_name: str,
        display_name: str,
        params: dict | None,
    ) -> LlmModel:
        model = LlmModel(
            provider=provider,
            model_name=model_name,
            display_name=display_name,
            params=params,
            is_active=False,
        )
        self.db.add(model)
        await self.db.flush()
        return model

    async def get_by_id(self, model_id: int) -> LlmModel | None:
        result = await self.db.execute(select(LlmModel).where(LlmModel.id == model_id))
        return result.scalar_one_or_none()

    async def update(self, model: LlmModel, fields: dict) -> None:
        for key, value in fields.items():
            setattr(model, key, value)
        await self.db.flush()

    async def delete(self, model: LlmModel) -> None:
        await self.db.delete(model)
        await self.db.flush()

    async def deactivate_all(self) -> None:
        await self.db.execute(update(LlmModel).values(is_active=False))

    async def set_active(self, model: LlmModel) -> None:
        model.is_active = True
        await self.db.flush()

    async def create_audit_log(
        self,
        admin_id: int,
        action: str,
        target_type: str,
        target_id: str,
        detail: dict,
        ip_address: str | None,
    ) -> None:
        self.db.add(
            AdminAuditLog(
                admin_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
                ip_address=ip_address,
            )
        )
