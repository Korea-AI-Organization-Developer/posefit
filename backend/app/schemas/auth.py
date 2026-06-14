from app.schemas.base import CamelModel
from app.schemas.user import UserRead


class AuthSocialCallbackRequest(CamelModel):
    """프론트가 OAuth provider 에서 받은 code 를 전달 (SPA code-exchange)."""

    code: str
    redirect_uri: str
    state: str | None = None


class AuthSocialCallbackResponse(CamelModel):
    access_token: str
    refresh_token: str
    access_token_expires_in: int
    is_new_user: bool
    user: UserRead


class AuthRefreshRequest(CamelModel):
    refresh_token: str


class AuthRefreshResponse(CamelModel):
    access_token: str
    access_token_expires_in: int
