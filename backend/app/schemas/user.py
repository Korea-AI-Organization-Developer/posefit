from datetime import date, datetime
from enum import Enum

from pydantic import Field, field_validator

from app.models.enums import Gender
from app.schemas.base import CamelModel


class RegistrationStep(str, Enum):
    """가입 진행 단계 — DB 미저장(Derived). 약관→디테일 순으로 채워진다."""

    agreements_required = "agreements_required"
    detail_required = "detail_required"
    complete = "complete"


# ─── User ──────────────────────────────────────────────────────────────────
class UserDetailRead(CamelModel):
    height: float | None = None
    weight: float | None = None
    birthdate: date
    gender: Gender


class UserRead(CamelModel):
    id: int
    # email/avatarUrl 은 users 미저장 — 대표(최초 연동) social_account 에서 derive.
    email: str | None = None
    avatar_url: str | None = None
    nickname: str
    role: str
    status: str
    registration_step: RegistrationStep
    detail: UserDetailRead | None = None
    created_at: datetime


class UserUpdateRequest(CamelModel):
    nickname: str = Field(min_length=1, max_length=50)


class UserDetailUpsertRequest(CamelModel):
    height: float | None = Field(default=None, ge=50, le=250)
    weight: float | None = Field(default=None, ge=20, le=300)
    birthdate: date
    gender: Gender

    @field_validator("birthdate")
    @classmethod
    def _not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("생년월일은 미래 날짜일 수 없습니다")
        return v


# ─── Agreement ─────────────────────────────────────────────────────────────
class AgreementRead(CamelModel):
    id: int
    tos_agreed: bool
    privacy_agreed: bool
    biometric_agreed: bool
    marketing_agreed: bool
    agreed_at: datetime


class AgreementCreateRequest(CamelModel):
    tos_agreed: bool
    privacy_agreed: bool
    biometric_agreed: bool
    marketing_agreed: bool = False


# ─── Social ────────────────────────────────────────────────────────────────
class SocialAccountRead(CamelModel):
    provider: str
    provider_uid: str
    provider_email: str | None = None
    linked_at: datetime  # social_accounts.created_at


