import asyncio
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai.llm.langgraph_V2 import _answer_payload_from_final_feedback, posefit_graph
from ai.pose.mediapipe_estimatorV2 import vision
from app.models.enums import SessionStatus
from app.repositories.exercise import ExerciseRepository
from app.repositories.feedback import FeedbackRepository
from app.repositories.workout_session import WorkoutSessionRepository
from app.schemas.feedback import FeedbackRead, FeedbackTimelineItem
from app.schemas.workout import StopSessionResponse
from app.schemas.workout_session import (
    EmbeddedExercise,
    WorkoutSessionCreateRequest,
    WorkoutSessionListResponse,
    WorkoutSessionRead,
    WorkoutSessionSummary,
)

UPLOAD_DIR = Path("uploads/workout_sessions")
# 저장 영상 루트 — 컨테이너에서는 볼륨 마운트 경로(/app/saves)를 env 로 주입.
# 미설정 시 로컬 개발용 기본값.
VIDEO_SAVE_BASE = Path(os.getenv("VIDEO_SAVE_BASE", "saves"))



class WorkoutSessionService:
    def __init__(self, db: AsyncSession):
        self.repo = WorkoutSessionRepository(db)
        self.exercise_repo = ExerciseRepository(db)
        self.feedback_repo = FeedbackRepository(db)
        self.db = db

    async def list_saved(
        self,
        user_id: int,
        exercise_id: int | None = None,
        cursor: int | None = None,
        limit: int = 6,
    ) -> WorkoutSessionListResponse:
        rows = await self.repo.list_saved(user_id, exercise_id, cursor, limit)
        has_next = len(rows) > limit
        items = rows[:limit]
        summaries = [
            WorkoutSessionSummary(
                id=s.id,
                exercise=EmbeddedExercise(id=s.exercise.id, name_ko=s.exercise.name_ko),
                status=s.status,
                started_at=s.started_at,
                ended_at=s.ended_at,
                duration_sec=(
                    int((s.ended_at - s.started_at).total_seconds()) if s.ended_at else None
                ),
                score=s.score,
                rep_count=s.rep_count,
                saved=s.saved,
                video_url=s.video_url,
            )
            for s in items
        ]
        return WorkoutSessionListResponse(
            items=summaries,
            next_cursor=items[-1].id if has_next and items else None,
        )

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

        filename = f"{user_id}_{exercise_id}.mp4"
        file_path = UPLOAD_DIR / filename

        content = await video.read()
        file_path.write_bytes(content)

        video_url = f"/uploads/workout_sessions/{filename}"
        workout_point_model = vision
        vision_result = workout_point_model(
                                        video_url = video_url,
                                        user_id = user_id,
                                        exercise_id= exercise_id,
                                        start_at=start_at,
                                        fps= None  # None = 원본 fps 그대로 전체 프레임 처리
                                    )
        points = vision_result["normalized"]
        json_url = str(vision_result["norm_json_path"])

        session = await self.repo.create(
            user_id=user_id,
            exercise_id=exercise_id,
            started_at=start_at,
            ended_at=end_at,
            video_url=video_url,
            json_url=json_url,
        )
        # 구조화 자세분석 결과 저장 (리포트 종합평가 long_term 입력). 실패해도 세션 저장엔 영향 없음.
        await self._save_pose_analysis(session.id, user_id, exercise_id, points)

        # 이 세트의 LLM 피드백을 만들어 feedbacks 에 저장한다(generatedBy='llm').
        # → 이후 GET /exercises/{id}/feedbacks 와 :summary 가 읽어가는 원본이 된다.
        exercise = await self.exercise_repo.get_by_id(exercise_id)
        exercise_name = exercise.name_ko if exercise else ""
        if exercise_id == 1:
            rule_config_path = "ai/llm/config/lunge_rule_config_mediapipe.json"
        elif exercise_id == 2:
            rule_config_path = "ai/llm/config/plank_rule_config_mediapipe.json"
        elif exercise_id == 3:
            rule_config_path = "ai/llm/config/pushup_rule_config_mediapipe.json"
        elif exercise_id == 4:
            rule_config_path = "ai/llm/config/ohp_rule_config_mediapipe.json"
        else:
            rule_config_path = ""

        # "set" 분기 강제:
        # route_feedback은 today_set_results → "daily", historical_* → "long_term", 그 외 → "set" 순으로 분기한다.
        # 아래 state에는 today_set_results / historical_analysis_results / historical_feedback_texts를
        # 의도적으로 포함하지 않아 반드시 "set" 경로로만 진입한다.
        state = {
            "normalized_pose": points,
            "exercise": exercise_name,
            "camera_view": "측면",
            "rule_config_path": rule_config_path,
            "exercise_id": exercise_id,
        }
        result: dict = dict(await asyncio.to_thread(posefit_graph.invoke, state))
        final_fb = result.get("final_feedback", {})

        score_pct = result.get("analysis_result", {}).get("score_summary", {}).get("time_weighted_score_pct")
        if score_pct is not None:
            session.score = score_pct

        # coaching 텍스트만 DB에 저장 (summary·timeline은 응답 전용)
        # "set" 분기: final_feedback = {raw, summary, timestamp} — "feedback_text.coaching" 구조 아님
        comment = final_fb.get("raw") or final_fb.get("feedback_text", {}).get("coaching", "")
        feedback = await self.feedback_repo.create(session_id=session.id, content=comment)
        await self.db.commit()
        # created_at(서버 기본값)·확정 값을 채우기 위해 다시 읽어온다.
        await self.db.refresh(feedback)

        # LangGraph 추가 출력 추출 — DB 미저장, 이번 응답에만 포함
        payload = _answer_payload_from_final_feedback(final_fb)
        summary_text = payload.get("summary") or None
        raw_timeline = payload.get("timestamp") or []
        timeline_items = [
            FeedbackTimelineItem(
                timestamp=item["time"],       # LangGraph: time → 구간 시각 레이블
                comment=item["coaching"],     # LangGraph: coaching → 구간 설명
                is_good=bool(item["pose"]),   # LangGraph: pose → True=정상, False=오류
            )
            for item in raw_timeline
            if isinstance(item, dict) and item.get("time")
        ] or None

        feedback_read = FeedbackRead.model_validate(feedback).model_copy(update={
            "summary": summary_text,
            "timeline": timeline_items,
        })

        return StopSessionResponse(
            session_id=session.id,
            video_url=video_url,
            score=float(session.score) if session.score is not None else None,
            feedback=feedback_read,
        )

    async def _save_pose_analysis(
        self, session_id: int, user_id: int, exercise_id: int, normalized_pose
    ) -> None:
        """정규화 pose → 분석 노드 실행 → workout_analyses 저장. 어떤 실패든 무시."""
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
        rel_path = Path(str(user_id)) / exercise_name / f"{date_str}_{session_id}.mp4"
        dest_dir = VIDEO_SAVE_BASE / rel_path.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = VIDEO_SAVE_BASE / rel_path

        temp_path = Path(session.video_url.lstrip("/"))
        if not temp_path.exists():
            raise HTTPException(status_code=409, detail="임시 영상 파일이 존재하지 않습니다")

        shutil.move(str(temp_path), str(dest_path))
        # /saves/... 상대 경로로 저장 — Next.js 프록시(/api/video/saves/...)가 서빙
        await self.repo.update_saved(session, f"/saves/{rel_path.as_posix()}")
        await self.db.commit()

    async def discard_session(self, session_id: int, user_id: int) -> None:
        session = await self.repo.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        if session.saved:
            raise HTTPException(status_code=409, detail="이미 저장된 세션은 폐기할 수 없습니다")

        if session.video_url:
            url = session.video_url
            if url.startswith("/saves/"):
                file_path = VIDEO_SAVE_BASE / url.removeprefix("/saves/")
            else:
                file_path = Path(url.lstrip("/"))
            if file_path.exists():
                file_path.unlink()

        await self.db.commit()

    async def next_session(self, session_id: int, user_id: int):
        session = await self.repo.get_by_id(session_id)
        if session is None or session.user_id != user_id:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

        new_session = await self.repo.create_in_progress(user_id, session.exercise_id)
        await self.db.commit()
        await self.db.refresh(new_session)
        return new_session
