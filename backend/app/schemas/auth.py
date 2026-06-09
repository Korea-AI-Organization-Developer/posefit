from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Gender


class SignupCompleteRequest(BaseModel):
    temp_token: str
    nickname: str = Field(..., min_length=2, max_length=20)
    birthdate: date
    gender: Gender
    height: float | None = Field(None, ge=50, le=250)
    weight: float | None = Field(None, ge=20, le=300)
    tos_agreed: bool
    privacy_agreed: bool
    biometric_agreed: bool
    marketing_agreed: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    role: str
    status: str
