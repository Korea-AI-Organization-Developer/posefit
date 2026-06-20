from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.admin_llm import AdminLlmRepository
from app.schemas.admin_llm import LlmModelCreateRequest, LlmModelResponse, LlmModelUpdateRequest


class AdminLlmService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminLlmRepository(db)

    async def list_models(self) -> list[LlmModelResponse]:
        models = await self.repo.list_all()
        return [LlmModelResponse.model_validate(m) for m in models]

    async def create_model(self, body: LlmModelCreateRequest) -> LlmModelResponse:
        model = await self.repo.create(
            provider=body.provider,
            model_name=body.model_name,
            display_name=body.display_name,
            params=body.params,
        )
        await self.db.commit()
        await self.db.refresh(model)
        return LlmModelResponse.model_validate(model)

    async def update_model(self, model_id: int, body: LlmModelUpdateRequest) -> LlmModelResponse:
        model = await self.repo.get_by_id(model_id)
        if model is None:
            raise HTTPException(status_code=404, detail="LLM 모델을 찾을 수 없습니다")

        fields = {k: v for k, v in body.model_dump().items() if k in body.model_fields_set}
        if fields:
            await self.repo.update(model, fields)
        await self.db.commit()
        await self.db.refresh(model)
        return LlmModelResponse.model_validate(model)

    async def delete_model(self, model_id: int) -> None:
        model = await self.repo.get_by_id(model_id)
        if model is None:
            raise HTTPException(status_code=404, detail="LLM 모델을 찾을 수 없습니다")
        if model.is_active:
            raise HTTPException(status_code=400, detail="활성 모델은 삭제할 수 없습니다. 먼저 다른 모델로 교체하세요")
        await self.repo.delete(model)
        await self.db.commit()

    async def activate_model(
        self,
        model_id: int,
        admin_id: int,
        ip_address: str | None,
    ) -> LlmModelResponse:
        model = await self.repo.get_by_id(model_id)
        if model is None:
            raise HTTPException(status_code=404, detail="LLM 모델을 찾을 수 없습니다")

        await self.repo.deactivate_all()
        await self.repo.set_active(model)
        await self.repo.create_audit_log(
            admin_id=admin_id,
            action="activate_llm",
            target_type="llm_model",
            target_id=str(model_id),
            detail={"modelName": model.model_name, "provider": model.provider.value},
            ip_address=ip_address,
        )
        await self.db.commit()
        await self.db.refresh(model)
        return LlmModelResponse.model_validate(model)
