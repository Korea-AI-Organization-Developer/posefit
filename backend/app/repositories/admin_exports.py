from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import AdminAuditLog
from app.models.enums import SessionStatus
from app.models.workout import KeypointFrame, WorkoutSession


class AdminExportsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_sessions(
        self,
        status: SessionStatus | None,
        exercise_id: int | None,
        from_dt: datetime | None,
        to_dt: datetime | None,
        page: int,
        size: int,
    ) -> tuple[list[WorkoutSession], int]:
        base = select(WorkoutSession).options(selectinload(WorkoutSession.exercise))

        if status is not None:
            base = base.where(WorkoutSession.status == status)
        if exercise_id is not None:
            base = base.where(WorkoutSession.exercise_id == exercise_id)
        if from_dt is not None:
            base = base.where(WorkoutSession.started_at >= from_dt)
        if to_dt is not None:
            base = base.where(WorkoutSession.started_at <= to_dt)

        total: int = (
            await self.db.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()

        sessions = (
            await self.db.execute(
                base.order_by(WorkoutSession.started_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()

        return list(sessions), total

    async def get_session_with_frames(
        self, session_id: int
    ) -> tuple[WorkoutSession, list[KeypointFrame]] | None:
        session = (
            await self.db.execute(
                select(WorkoutSession)
                .options(selectinload(WorkoutSession.exercise))
                .where(WorkoutSession.id == session_id)
            )
        ).scalar_one_or_none()

        if session is None:
            return None

        frames = (
            await self.db.execute(
                select(KeypointFrame)
                .where(KeypointFrame.session_id == session_id)
                .order_by(KeypointFrame.frame_index)
            )
        ).scalars().all()

        return session, list(frames)

    async def get_sessions_with_frames(
        self,
        exercise_id: int | None,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> list[tuple[WorkoutSession, list[KeypointFrame]]]:
        base = (
            select(WorkoutSession)
            .options(selectinload(WorkoutSession.exercise))
            .where(WorkoutSession.status == SessionStatus.completed)
        )

        if exercise_id is not None:
            base = base.where(WorkoutSession.exercise_id == exercise_id)
        if from_dt is not None:
            base = base.where(WorkoutSession.started_at >= from_dt)
        if to_dt is not None:
            base = base.where(WorkoutSession.started_at <= to_dt)

        sessions = (
            await self.db.execute(base.order_by(WorkoutSession.started_at.asc()))
        ).scalars().all()

        result = []
        for s in sessions:
            frames = (
                await self.db.execute(
                    select(KeypointFrame)
                    .where(KeypointFrame.session_id == s.id)
                    .order_by(KeypointFrame.frame_index)
                )
            ).scalars().all()
            result.append((s, list(frames)))

        return result

    async def create_audit_log(
        self,
        admin_id: int,
        action: str,
        target_type: str,
        target_id: str,
        detail: dict,
        ip_address: str | None,
    ) -> None:
        self.db.add(
            AdminAuditLog(
                admin_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
                ip_address=ip_address,
            )
        )
