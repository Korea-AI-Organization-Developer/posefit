"""관리자(운영) 도메인 모델.

소비자(users)와 운영자(admin_accounts)의 신원을 완전히 분리한다.
- admin_accounts : 전용 이메일/비밀번호 자격증명 (소비자 Google OAuth 와 무관)
- llm_models     : RAG 피드백 생성용 LLM 모델 레지스트리 (활성 모델 1개)
- admin_audit_logs : 관리자 행위 감사 로그 (append-only)
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AdminRole, AdminStatus, LlmProvider
from app.models.mixins import TimestampMixin


class AdminAccount(Base, TimestampMixin):
    __tablename__ = "admin_accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, comment="로그인 ID(이메일)."
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="passlib bcrypt 해시."
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[AdminRole] = mapped_column(
        Enum(AdminRole),
        nullable=False,
        server_default=text("'admin'"),
        comment="super_admin 만 관리자 계정·감사 로그 관리 가능.",
    )
    status: Mapped[AdminStatus] = mapped_column(
        Enum(AdminStatus), nullable=False, server_default=text("'active'"), comment="활성 | 비활성"
    )
    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="refresh 토큰 무효화용. 로그아웃 시 +1.",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    audit_logs: Mapped[list["AdminAuditLog"]] = relationship(back_populates="admin")


class LlmModel(Base, TimestampMixin):
    __tablename__ = "llm_models"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider: Mapped[LlmProvider] = mapped_column(Enum(LlmProvider), nullable=False)
    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="API 식별자. 예: gemini-3.5-flash"
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="UI 표시명.")
    params: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="기본 호출 파라미터(temperature 등)."
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("0"),
        comment="활성 모델 여부. 정확히 1개 행만 true 를 유지한다(교체 시 트랜잭션).",
    )


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admin_accounts.id"), nullable=False)
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="예: export_keypoints, activate_llm, update_user_status"
    )
    target_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="user | exercise | session | llm_model"
    )
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="필터 조건·변경 전후값 등 부가 정보."
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )

    admin: Mapped["AdminAccount"] = relationship(back_populates="audit_logs")
