from datetime import date, datetime

from app.models.enums import Gender, UserRole, UserStatus
from app.schemas.base import CamelModel


class AdminUserListItem(CamelModel):
    id: int
    nickname: str
    email: str | None
    role: UserRole
    status: UserStatus
    created_at: datetime


class AdminUserPage(CamelModel):
    total: int
    page: int
    size: int
    items: list[AdminUserListItem]


class AdminUserUpdateRequest(CamelModel):
    status: UserStatus


class AdminUserDetail(CamelModel):
    id: int
    nickname: str
    email: str | None
    role: UserRole
    status: UserStatus
    created_at: datetime
    withdrawn_at: datetime | None
    birthdate: date | None
    gender: Gender | None
    height: float | None
    weight: float | None
    face_registered: bool
    marketing_agreed: bool | None
    session_count: int
