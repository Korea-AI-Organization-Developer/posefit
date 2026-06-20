from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.admin import AdminAccount
from app.schemas.admin_llm import LlmModelCreateRequest, LlmModelResponse, LlmModelUpdateRequest
from app.services.admin_llm import AdminLlmService

router = APIRouter(prefix="/admin/llm", tags=["Admin LLM"])


@router.get("/models", response_model=list[LlmModelResponse])
async def list_llm_models(
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminLlmService(db).list_models()


@router.post("/models", response_model=LlmModelResponse, status_code=201)
async def create_llm_model(
    body: LlmModelCreateRequest,
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminLlmService(db).create_model(body)


@router.patch("/models/{model_id}", response_model=LlmModelResponse)
async def update_llm_model(
    model_id: int,
    body: LlmModelUpdateRequest,
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminLlmService(db).update_model(model_id, body)


@router.delete("/models/{model_id}", status_code=204)
async def delete_llm_model(
    model_id: int,
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await AdminLlmService(db).delete_model(model_id)


@router.post("/models/{model_id}:activate", response_model=LlmModelResponse)
async def activate_llm_model(
    model_id: int,
    request: Request,
    admin: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await AdminLlmService(db).activate_model(model_id, admin.id, ip)
