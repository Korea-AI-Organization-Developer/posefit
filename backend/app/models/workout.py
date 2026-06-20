from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FeedbackSeverity, FeedbackSource, SessionStatus
from app.models.mixins import TimestampMixin, _UTCDateTime


class WorkoutSession(Base, TimestampMixin):
    __tablename__ = "workout_sessions"
    __table_args__ = (Index("idx_user_started", "user_id", "started_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), nullable=False, server_default=text("'in_progress'")
    )
    started_at: Mapped[datetime] = mapped_column(
        _UTCDateTime(fsp=6), nullable=False, comment="세션 시작 시각(KST)."
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        _UTCDateTime(fsp=6), nullable=True, comment="세션 종료 시각(KST). 진행 중이면 NULL."
    )
    score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="0~100점. 완료 시에만 채워짐."
    )
    rep_count: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True), nullable=True, comment="반복 횟수(횟수 기반 운동)."
    )
    hold_sec: Mapped[int | None] = mapped_column(
        INTEGER(unsigned=True), nullable=True, comment="자세 유지 시간(초)(시간 기반 운동)."
    )
    saved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), comment="사용자가 영상을 저장했는지 여부."
    )
    video_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="개인정보. saved=true일 때 오브젝트 스토리지 URL."
    )

    user: Mapped["User"] = relationship(back_populates="sessions")
    exercise: Mapped["Exercise"] = relationship(back_populates="sessions")
    frames: Mapped[list["KeypointFrame"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    feedbacks: Mapped[list["Feedback"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class KeypointFrame(Base):
    __tablename__ = "keypoint_frames"
    __table_args__ = (UniqueConstraint("session_id", "frame_index", name="uq_session_frame"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id"), nullable=False)
    frame_index: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="세션 내 프레임 인덱스(0부터 시작)."
    )
    timestamp_ms: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), nullable=False, comment="started_at 기준 경과 밀리초."
    )
    keypoints: Mapped[dict] = mapped_column(JSON, nullable=False, comment="정규화된 관절 키포인트(0~1).")
    bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="사람 바운딩 박스 [x, y, w, h].")

    session: Mapped["WorkoutSession"] = relationship(back_populates="frames")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="사용자에게 보여줄 자연어 피드백.")
    severity: Mapped[FeedbackSeverity] = mapped_column(
        Enum(FeedbackSeverity), nullable=False, server_default=text("'info'")
    )
    generated_by: Mapped[FeedbackSource] = mapped_column(Enum(FeedbackSource), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        _UTCDateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)")
    )

    session: Mapped["WorkoutSession"] = relationship(back_populates="feedbacks")


class WorkoutDailyStat(Base):
    __tablename__ = "workout_daily_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", "stat_date", name="uq_user_exercise_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), nullable=False)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    session_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), nullable=False, server_default=text("0")
    )
    total_duration_sec: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), nullable=False, server_default=text("0")
    )
    avg_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    best_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
