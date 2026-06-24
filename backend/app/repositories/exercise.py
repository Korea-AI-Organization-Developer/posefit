# func: SQL의 집계 함수(avg, count 등)를 파이썬에서 부르는 도구. 여기선 func.avg(평균)를 쓴다.
# select: "SELECT ... FROM ..." 조회문을 파이썬 코드로 만드는 도구.
from sqlalchemy import case, func, select

# AsyncSession: 데이터베이스와의 "비동기 연결(세션)" 타입. 이걸로 쿼리를 실행한다.
from sqlalchemy.ext.asyncio import AsyncSession

# Exercise: exercises 테이블의 파이썬 표현(모델). 운동 종목 데이터.
from app.models.exercise import Exercise
# WorkoutDailyStat: workout_daily_stats 테이블의 모델. 사용자별·운동별·날짜별 통계(평균 점수 등).
from app.models.workout import WorkoutDailyStat


# ExerciseRepository: "운동 데이터를 DB에서 꺼내오는" 일만 담당하는 층(repository).
#                     규칙: 여기서는 조회/추가만 하고, 저장 확정(commit)은 하지 않는다.
class ExerciseRepository:
    # __init__: 이 클래스를 만들(생성할) 때 호출되는 함수. DB 세션을 받아 보관해 둔다.
    def __init__(self, db: AsyncSession):
        self.db = db                 # 받은 DB 세션을 self.db에 저장 → 아래 메서드들이 self.db로 쿼리 실행.

    # list: 운동 목록을 (각 운동 + 그 사용자의 평균 점수)와 함께 조회한다.
    #   user_id    = 평균 점수를 계산할 대상 사용자
    #   active_only = True면 노출 중(is_active=True)인 운동만
    async def list(self, user_id: int, active_only: bool = True):
        # ── ① 서브쿼리: "이 사용자"의 운동별 평균 점수표를 먼저 만든다 ─────────────
        # 큰 조회 안에 들어가는 작은 조회. 운동마다 평균 점수 한 줄을 미리 계산해 둔다.
        avg_subq = (
            select(
                WorkoutDailyStat.exercise_id,                              # 어떤 운동의 (기준 열)
                func.avg(WorkoutDailyStat.avg_score).label("user_avg_score"),  # 그 운동의 평균 점수. label로 이름 붙임.
            )
            .where(WorkoutDailyStat.user_id == user_id)   # 조건: 이 사용자의 기록만 골라서
            .group_by(WorkoutDailyStat.exercise_id)        # 운동별로 묶어서(그룹) 평균을 낸다
            .subquery()                                    # 이 조회를 "서브쿼리"로 만들어 아래에서 재사용
        )

        # ── ② 본 조회: 운동 목록에 ①의 평균 점수를 이어 붙인다 ──────────────────
        # outerjoin = LEFT JOIN. 운동(왼쪽)은 전부 살리고, 평균이 없는 운동은 그 자리에 NULL을 채운다.
        # (일반 JOIN이면 한 번도 안 한 운동이 목록에서 통째로 빠져버리므로 outerjoin을 쓴다.)
        stmt = select(Exercise, avg_subq.c.user_avg_score).outerjoin(
            avg_subq, Exercise.id == avg_subq.c.exercise_id  # 운동.id == 서브쿼리.exercise_id 끼리 연결
        )
        # active_only가 True면, 노출 중인 운동만 남기는 조건을 추가한다.
        if active_only:
            stmt = stmt.where(Exercise.is_active.is_(True))   # WHERE is_active = TRUE

        # ── ③ 정렬: 플랭크 → 런지 → 나머지(id 순) ──────────────────────────────
        stmt = stmt.order_by(
            case(
                (Exercise.name_en == "Plank", 1),
                (Exercise.name_en == "Lunge", 2),
                else_=Exercise.id + 10,
            )
        )

        # ── ④ 실행: 위에서 조립한 조회문을 DB에 보내 결과를 받는다 ────────────────
        result = await self.db.execute(stmt)   # await: DB가 답할 때까지 기다림(그동안 다른 요청 처리 가능).
        return result.all()                    # (Exercise 객체, 평균점수) 쌍들의 목록을 그대로 반환.

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        result = await self.db.execute(select(Exercise).where(Exercise.id == exercise_id))
        return result.scalar_one_or_none()
