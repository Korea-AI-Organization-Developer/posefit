import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SessionStatus
from app.repositories.exercise import ExerciseRepository
from app.repositories.workout_session import WorkoutSessionRepository
from app.schemas.workout import StopSessionResponse
from app.schemas.workout_session import WorkoutSessionCreateRequest, WorkoutSessionRead

# 포즈 추정 모델
from ai.pose.mediapipe_estimatorV2 import vision

UPLOAD_DIR = Path("uploads/workout_sessions")
VIDEO_SAVE_BASE = Path("C:/posefit_saves")


async def getLlmFeedback() -> str:
    """LLM 코멘트 생성 (추후 구현 예정)."""
    return "getLlmFeedback()"


class WorkoutSessionService:
    def __init__(self, db: AsyncSession):
        self.repo = WorkoutSessionRepository(db)
        self.exercise_repo = ExerciseRepository(db)
        self.db = db

    async def create(self, user_id: int, req: WorkoutSessionCreateRequest) -> WorkoutSessionRead:
        exercise = await self.exercise_repo.get_by_id(req.exercise_id)
        if exercise is None or not exercise.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않거나 비활성화된 운동 종목입니다",
            )
        session = await self.repo.create_in_progress(user_id, req.exercise_id)
        await self.db.commit()
        await self.db.refresh(session)
        return WorkoutSessionRead.model_validate(session)

    async def get(self, user_id: int, session_id: int) -> WorkoutSessionRead:
        session = await self.repo.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다")
        return WorkoutSessionRead.model_validate(session)

    async def delete(self, user_id: int, session_id: int) -> None:
        session = await self.repo.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다")
        await self.repo.delete(session)
        await self.db.commit()

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
        workout_point_model = vision
        points = workout_point_model(
                                        video_url = video_url,
                                        user_id = user_id,
                                        exercise_id= exercise_id,
                                        start_at=start_at,
                                        fps= 30  # fps변경 시 이곳을 참조
                                    )
        session = await self.repo.create(
            user_id=user_id,
            exercise_id=exercise_id,
            started_at=start_at,
            ended_at=end_at,
            video_url=video_url,
        )
        await self.db.commit()

        # 구조화 자세분석 결과 저장 (리포트 종합평가 long_term 입력). 실패해도 세션 저장엔 영향 없음.
        await self._save_pose_analysis(session.id, user_id, exercise_id, points)

        # comment = await getLlmFeedback(피드백 위치 , points)
        comment = await getLlmFeedback()
        return StopSessionResponse(session_id=session.id, video_url=video_url, comment=comment)

    async def _save_pose_analysis(
        self, session_id: int, user_id: int, exercise_id: int, normalized_pose
    ) -> None:
        """정규화 pose → 분석 노드 실행 → workout_analyses 저장. 어떤 실패든 무시."""
        import asyncio
        import logging

        from app.models.workout import WorkoutAnalysis

        try:
            exercise = await self.exercise_repo.get_by_id(exercise_id)
            if exercise is None or not isinstance(normalized_pose, dict):
                return

            from ai.llm.analysis_runner import run_pose_analysis

            analysis = await asyncio.to_thread(
                run_pose_analysis, normalized_pose, exercise.name_ko
            )
            if not analysis:  # rule config 미존재 종목 등 → 저장 스킵
                return

            self.db.add(WorkoutAnalysis(
                session_id=session_id,
                user_id=user_id,
                exercise_id=exercise_id,
                analysis_result=analysis,
                overall_status=analysis.get("overall_status"),
            ))
            await self.db.commit()
        except Exception as exc:  # noqa: BLE001 — 분석 저장 실패가 세션 저장을 깨지 않도록
            logging.getLogger(__name__).warning("자세분석 저장 실패(무시): %s", exc)

    async def save_video(self, session_id: int, user_id: int) -> None:
        session = await self.repo.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        if session.status != SessionStatus.completed:
            raise HTTPException(status_code=409, detail="SESSION_NOT_COMPLETED")
        if not session.video_url:
            raise HTTPException(status_code=409, detail="저장할 영상이 없습니다")

        exercise = await self.exercise_repo.get_by_id(session.exercise_id)
        exercise_name = exercise.name_ko if exercise else str(session.exercise_id)

        date_str = session.started_at.strftime("%Y%m%d")
        dest_dir = VIDEO_SAVE_BASE / str(user_id) / exercise_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{date_str}_{session_id}.mp4"

        temp_path = Path(session.video_url.lstrip("/"))
        if not temp_path.exists():
            raise HTTPException(status_code=409, detail="임시 영상 파일이 존재하지 않습니다")

        shutil.move(str(temp_path), str(dest_path))
        await self.repo.update_saved(session, str(dest_path))
        await self.db.commit()

    async def discard_session(self, session_id: int, user_id: int) -> None:
        session = await self.repo.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        if session.saved:
            raise HTTPException(status_code=409, detail="이미 저장된 세션은 폐기할 수 없습니다")

        if session.video_url:
            temp_path = Path(session.video_url.lstrip("/"))
            if temp_path.exists():
                temp_path.unlink()

        await self.db.commit()

    async def next_session(self, session_id: int, user_id: int):
        session = await self.repo.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

        new_session = await self.repo.create_in_progress(user_id, session.exercise_id)
        await self.db.commit()
        await self.db.refresh(new_session)
        return new_session
