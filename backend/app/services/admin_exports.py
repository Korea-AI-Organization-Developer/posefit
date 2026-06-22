import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SessionStatus
from app.models.workout import KeypointFrame, WorkoutSession
from app.repositories.admin_exports import AdminExportsRepository
from app.schemas.admin_exports import AdminSessionListItem, AdminSessionPage, EmbeddedExercise


def _session_meta(s: WorkoutSession) -> dict:
    return {
        "sessionId": s.id,
        "exerciseId": s.exercise_id,
        "exerciseNameKo": s.exercise.name_ko if s.exercise else None,
        "status": s.status.value,
        "startedAt": s.started_at.isoformat() if s.started_at else None,
        "score": float(s.score) if s.score is not None else None,
    }


def _frame_dict(f: KeypointFrame) -> dict:
    return {
        "frameIndex": f.frame_index,
        "timestampMs": f.timestamp_ms,
        "keypoints": f.keypoints,
        "bbox": f.bbox,
    }


class AdminExportsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminExportsRepository(db)

    async def list_sessions(
        self,
        status: SessionStatus | None,
        exercise_id: int | None,
        from_dt: datetime | None,
        to_dt: datetime | None,
        page: int,
        size: int,
    ) -> AdminSessionPage:
        sessions, total = await self.repo.list_sessions(
            status, exercise_id, from_dt, to_dt, page, size
        )
        items = [
            AdminSessionListItem(
                id=s.id,
                exercise=EmbeddedExercise(id=s.exercise.id, name_ko=s.exercise.name_ko),
                status=s.status,
                started_at=s.started_at,
                ended_at=s.ended_at,
                score=s.score,
                rep_count=s.rep_count,
                hold_sec=s.hold_sec,
                saved=s.saved,
            )
            for s in sessions
        ]
        return AdminSessionPage(total=total, page=page, size=size, items=items)

    async def export_json(
        self,
        session_id: int,
        admin_id: int,
        ip_address: str | None,
    ) -> tuple[str, str]:
        result = await self.repo.get_session_with_frames(session_id)
        if result is None:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

        session, frames = result

        await self.repo.create_audit_log(
            admin_id=admin_id,
            action="export_keypoints",
            target_type="workout_session",
            target_id=str(session_id),
            detail={"format": "json", "frameCount": len(frames)},
            ip_address=ip_address,
        )
        await self.db.commit()

        payload = {
            "session": _session_meta(session),
            "frames": [_frame_dict(f) for f in frames],
        }
        filename = f"keypoints_session_{session_id}.json"
        return json.dumps(payload, ensure_ascii=False), filename

    async def export_jsonl(
        self,
        session_id: int | None,
        exercise_id: int | None,
        from_dt: datetime | None,
        to_dt: datetime | None,
        admin_id: int,
        ip_address: str | None,
    ) -> tuple[list[str], str]:
        if session_id is not None:
            result = await self.repo.get_session_with_frames(session_id)
            if result is None:
                raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
            pairs = [result]
            filename = f"keypoints_session_{session_id}.jsonl"
        else:
            pairs = await self.repo.get_sessions_with_frames(exercise_id, from_dt, to_dt)
            filename = "keypoints_export.jsonl"

        total_frames = sum(len(frames) for _, frames in pairs)

        await self.repo.create_audit_log(
            admin_id=admin_id,
            action="export_keypoints",
            target_type="workout_session",
            target_id=str(session_id) if session_id else "bulk",
            detail={
                "format": "jsonl",
                "sessionCount": len(pairs),
                "frameCount": total_frames,
            },
            ip_address=ip_address,
        )
        await self.db.commit()

        lines = []
        for session, frames in pairs:
            meta = _session_meta(session)
            for f in frames:
                lines.append(json.dumps({**meta, **_frame_dict(f)}, ensure_ascii=False))

        return lines, filename
