from datetime import datetime

from app.schemas.base import CamelModel


class AuditLogItem(CamelModel):
    id: int
    admin_id: int
    action: str
    target_type: str | None
    target_id: str | None
    detail: dict | None
    ip_address: str | None
    created_at: datetime


class AuditLogPage(CamelModel):
    total: int
    page: int
    size: int
    items: list[AuditLogItem]
