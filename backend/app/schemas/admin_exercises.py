from app.models.enums import ExerciseType
from app.schemas.base import CamelModel


class AdminExercise(CamelModel):
    id: int
    name_ko: str
    name_en: str | None
    description: str | None
    reference_video_url: str | None
    exercise_type: ExerciseType
    is_active: bool


class AdminExerciseCreateRequest(CamelModel):
    name_ko: str
    name_en: str | None = None
    description: str | None = None
    reference_video_url: str | None = None
    exercise_type: ExerciseType = ExerciseType.dynamic


class AdminExerciseUpdateRequest(CamelModel):
    name_ko: str | None = None
    name_en: str | None = None
    description: str | None = None
    reference_video_url: str | None = None
    exercise_type: ExerciseType | None = None
    is_active: bool | None = None
