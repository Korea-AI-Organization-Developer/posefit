import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.workout_session import WorkoutSessionRepository
from app.schemas.workout import StopSessionResponse

UPLOAD_DIR = Path("uploads/workout_sessions")


async def getLlmFeedback() -> str:
    """LLM 코멘트 생성 (추후 구현 예정)."""
    return "getLlmFeedback()"


class WorkoutSessionService:
    def __init__(self, db: AsyncSession):
        self.repo = WorkoutSessionRepository(db)
        self.db = db

    async def stop(
        self,
        user_id: int,
        exercise_id: int,
        start_at: datetime,
        end_at: datetime,
        video: UploadFile,
    ) -> StopSessionResponse:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        ext = Path(video.filename or "video.mp4").suffix or ".mp4"
        filename = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / filename

        content = await video.read()
        file_path.write_bytes(content)

        video_url = f"/uploads/workout_sessions/{filename}"

        await self.repo.create(
            user_id=user_id,
            exercise_id=exercise_id,
            started_at=start_at,
            ended_at=end_at,
            video_url=video_url,
        )
        await self.db.commit()

        comment = await getLlmFeedback()

        return StopSessionResponse(video_url=video_url, comment=comment)
