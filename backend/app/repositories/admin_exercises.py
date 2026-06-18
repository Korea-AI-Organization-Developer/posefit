from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminAuditLog
from app.models.exercise import Exercise


class AdminExercisesRepository:
    """DB 접근만 담당 — commit 하지 않는다(트랜잭션은 service)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Exercise]:
        result = await self.db.execute(select(Exercise).order_by(Exercise.id))
        return list(result.scalars().all())

    async def create_exercise(
        self,
        name_ko: str,
        name_en: str | None,
        description: str | None,
        reference_video_url: str | None,
        exercise_type: str,
    ) -> Exercise:
        exercise = Exercise(
            name_ko=name_ko,
            name_en=name_en,
            description=description,
            reference_video_url=reference_video_url,
            exercise_type=exercise_type,
            is_active=False,
        )
        self.db.add(exercise)
        await self.db.flush()
        return exercise

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        result = await self.db.execute(select(Exercise).where(Exercise.id == exercise_id))
        return result.scalar_one_or_none()

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
