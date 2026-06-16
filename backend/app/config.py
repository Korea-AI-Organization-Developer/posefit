from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str

    # ─── Google OAuth (SPA code-exchange) ───
    # 콜백에서 프론트가 보낸 authorization code 를 이 자격증명으로 교환한다.
    # redirect_uri 는 프론트가 OAuth 에 쓴 값을 콜백 본문으로 받아 사용한다(여기 저장 안 함).
    google_client_id: str = ""
    google_client_secret: str = ""

    # ─── JWT ───
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # openapi: access 15분
    refresh_token_expire_days: int = 14  # openapi: refresh 14일

    class Config:
        env_file = ".env"


settings = Settings()
