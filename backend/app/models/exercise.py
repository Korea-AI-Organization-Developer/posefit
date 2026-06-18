from sqlalchemy import BigInteger, Boolean, Enum, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ExerciseType


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name_ko: Mapped[str] = mapped_column(String(100), nullable=False, comment="표시 이름(한글).")
    name_en: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="표시 이름(영문).")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_video_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="정답(모범) 영상 URL."
    )
    exercise_type: Mapped[ExerciseType] = mapped_column(
        Enum(ExerciseType),
        nullable=False,
        server_default=text("'dynamic'"),
        comment="정적운동 static | 동적운동 dynamic",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("0"), comment="운동 종목 노출 여부"
    )

    sessions: Mapped[list["WorkoutSession"]] = relationship(back_populates="exercise")