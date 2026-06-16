from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import DATETIME, VARBINARY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import Gender, UserRole, UserStatus
from app.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, comment="구글에서 받아온 이름이 기본")
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, server_default=text("'user'"), comment="사용자 | 관리자"
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), nullable=False, server_default=text("'active'"), comment="활성 | 탈퇴"
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
        comment="refresh 토큰 무효화용. 로그아웃 시 +1 → 이전에 발급된 refresh 토큰 전부 무효.",
    )

    detail: Mapped["UserDetail"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    social_accounts: Mapped[list["SocialAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    agreement: Mapped["Agreement"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    face_embedding: Mapped["FaceEmbedding"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sessions: Mapped[list["WorkoutSession"]] = relationship(back_populates="user")


class UserDetail(Base, TimestampMixin):
    __tablename__ = "user_details"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    height: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True, comment="cm (50~250)")
    weight: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True, comment="kg (20~300)")
    birthdate: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=False, comment="남성 | 여성 | 선택 안 함")

    user: Mapped["User"] = relationship(back_populates="detail")


class SocialAccount(Base, TimestampMixin):
    __tablename__ = "social_accounts"
    __table_args__ = (UniqueConstraint("provider", "provider_uid", name="uq_provider_uid"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, comment="google")
    provider_uid: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="개인정보. 소셜 제공자 측 사용자 식별자."
    )
    provider_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="개인정보. 소셜 제공자 이메일(없을 수 있음)."
    )
    provider_avatar_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="개인정보. 소셜 제공자 프로필 사진 URL(없을 수 있음, 로그인 시 갱신).",
    )

    user: Mapped["User"] = relationship(back_populates="social_accounts")


class Agreement(Base):
    __tablename__ = "agreements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    tos_agreed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), comment="서비스 이용약관(필수)"
    )
    privacy_agreed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), comment="개인정보 수집·이용(필수)"
    )
    biometric_agreed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), comment="바이오정보(얼굴) 처리(필수)"
    )
    marketing_agreed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), comment="마케팅 수신(선택)"
    )
    agreed_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )

    user: Mapped["User"] = relationship(back_populates="agreement")


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    embedding: Mapped[bytes] = mapped_column(
        VARBINARY(1024),
        nullable=False,
        comment="개인정보. dlib 128차원 float64 직렬화 (1024 bytes).",
    )
    model_version: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="임베딩 모델 버전. 동일 버전끼리만 비교 유효."
    )
    registered_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"), comment="등록날짜"
    )

    user: Mapped["User"] = relationship(back_populates="face_embedding")
