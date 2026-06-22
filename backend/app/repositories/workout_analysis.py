from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import WorkoutAnalysis


class WorkoutAnalysisRepository:
    """세션별 구조화 자세분석 결과(analysis_result)를 저장/조회한다."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: int,
        user_id: int,
        exercise_id: int,
        analysis_result: dict,
        overall_status: str | None,
    ) -> WorkoutAnalysis:
        row = WorkoutAnalysis(
            session_id=session_id,
            user_id=user_id,
            exercise_id=exercise_id,
            analysis_result=analysis_result,
            overall_status=overall_status,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def list_recent_results(
        self,
        user_id: int,
        exercise_id: int | None = None,
        limit: int = 30,
    ) -> list[dict]:
        """리포트 종합평가용 — 최신순 analysis_result(dict) 목록."""
        stmt = select(WorkoutAnalysis.analysis_result).where(
            WorkoutAnalysis.user_id == user_id
        )
        if exercise_id is not None:
            stmt = stmt.where(WorkoutAnalysis.exercise_id == exercise_id)
        stmt = stmt.order_by(WorkoutAnalysis.id.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return [r for r in result.scalars().all() if r]
