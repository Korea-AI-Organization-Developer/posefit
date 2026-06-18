from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.admin_exercises import AdminExercisesRepository
from app.schemas.admin_exercises import AdminExercise, AdminExerciseCreateRequest, AdminExerciseUpdateRequest


class AdminExercisesService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminExercisesRepository(db)

    async def list_exercises(self) -> list[AdminExercise]:
        exercises = await self.repo.list_all()
        return [AdminExercise.model_validate(ex) for ex in exercises]

    async def create_exercise(
        self,
        body: AdminExerciseCreateRequest,
        admin_id: int,
        ip_address: str | None,
    ) -> AdminExercise:
        exercise = await self.repo.create_exercise(
            name_ko=body.name_ko,
            name_en=body.name_en,
            description=body.description,
            reference_video_url=body.reference_video_url,
            exercise_type=body.exercise_type,
        )
        await self.repo.create_audit_log(
            admin_id=admin_id,
            action="create_exercise",
            target_type="exercise",
            target_id=str(exercise.id),
            detail={"name_ko": body.name_ko, "exercise_type": body.exercise_type.value},
            ip_address=ip_address,
        )
        await self.db.commit()
        await self.db.refresh(exercise)
        return AdminExercise.model_validate(exercise)

    async def update_exercise(
        self,
        exercise_id: int,
        body: AdminExerciseUpdateRequest,
        admin_id: int,
        ip_address: str | None,
    ) -> AdminExercise:
        exercise = await self.repo.get_by_id(exercise_id)
        if exercise is None:
            raise HTTPException(status_code=404, detail="운동 종목을 찾을 수 없습니다")

        for field in body.model_fields_set:
            setattr(exercise, field, getattr(body, field))

        await self.repo.create_audit_log(
            admin_id=admin_id,
            action="update_exercise",
            target_type="exercise",
            target_id=str(exercise_id),
            detail={f: getattr(body, f) for f in body.model_fields_set},
            ip_address=ip_address,
        )
        await self.db.commit()
        await self.db.refresh(exercise)
        return AdminExercise.model_validate(exercise)
