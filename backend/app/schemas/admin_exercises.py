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
