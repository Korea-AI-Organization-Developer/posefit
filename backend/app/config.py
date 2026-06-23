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

    # ─── LLM (Gemini) — 리포트 종합 평가 LangGraph 용 ───
    # 키가 비어 있으면 종합 평가는 규칙 기반으로 폴백한다.
    google_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    class Config:
        env_file = ".env"
        extra = "ignore"  # .env 에 모델이 모르는 키가 있어도 무시(기동 실패 방지)


settings = Settings()
