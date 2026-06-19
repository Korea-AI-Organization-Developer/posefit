from datetime import datetime

from app.models.enums import LlmProvider
from app.schemas.base import CamelModel


class LlmModelResponse(CamelModel):
    id: int
    provider: LlmProvider
    model_name: str
    display_name: str
    params: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LlmModelCreateRequest(CamelModel):
    provider: LlmProvider
    model_name: str
    display_name: str
    params: dict | None = None


class LlmModelUpdateRequest(CamelModel):
    model_name: str | None = None
    display_name: str | None = None
    params: dict | None = None
