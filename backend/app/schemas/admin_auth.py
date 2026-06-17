from datetime import datetime

from app.models.enums import AdminRole, AdminStatus
from app.schemas.base import CamelModel


class AdminLoginRequest(CamelModel):
    email: str
    password: str


class AdminRead(CamelModel):
    id: int
    email: str
    name: str
    role: AdminRole
    status: AdminStatus
    last_login_at: datetime | None
    created_at: datetime


class AdminTokenResponse(CamelModel):
    access_token: str
    refresh_token: str
    access_token_expires_in: int
    admin: AdminRead


class AdminRefreshRequest(CamelModel):
    refresh_token: str


class AdminRefreshResponse(CamelModel):
    access_token: str
    access_token_expires_in: int
