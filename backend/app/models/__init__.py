"""SQLAlchemy ORM 모델 (docs/erd.sql 기반).

모든 모델을 여기서 import 하여 Base.metadata 에 등록한다 (Alembic autogenerate 용).
"""

from app.models.admin import AdminAccount, AdminAuditLog, LlmModel
from app.models.exercise import Exercise
from app.models.user import (
    Agreement,
    FaceEmbedding,
    SocialAccount,
    User,
    UserDetail,
)
from app.models.workout import (
    Feedback,
    KeypointFrame,
    WorkoutAnalysis,
    WorkoutDailyStat,
    WorkoutSession,
)

__all__ = [
    "User",
    "UserDetail",
    "SocialAccount",
    "Agreement",
    "FaceEmbedding",
    "Exercise",
    "WorkoutSession",
    "KeypointFrame",
    "Feedback",
    "WorkoutAnalysis",
    "WorkoutDailyStat",
    "AdminAccount",
    "LlmModel",
    "AdminAuditLog",
]
