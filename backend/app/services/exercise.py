# AsyncSession: DB 비동기 연결(세션) 타입. router에서 받아 repository로 넘긴다.
from sqlalchemy.ext.asyncio import AsyncSession

# User: 로그인한 사용자의 모델(users 테이블). user.id로 "누구의 평균인지" 구분한다.
from app.models.user import User
# ExerciseRepository: 바로 위에서 본 DB 조회 담당 층. service가 이걸 불러 쓴다.
from app.repositories.exercise import ExerciseRepository
# 응답 형식(스키마) 두 개를 가져온다. service가 조회 결과를 이 모양으로 변환해 돌려준다.
from app.schemas.exercise import ExerciseListResponse, ExerciseSummary


# ExerciseService: "무엇을 할지" 결정하는 로직 층. 이번 API는 단순해서 얇다(조회 결과를 응답 형식으로 정리만).
class ExerciseService:
    # 생성될 때 DB 세션을 받아, 그걸로 repository를 만들어 보관한다.
    def __init__(self, db: AsyncSession):
        self.repo = ExerciseRepository(db)   # 이 service 전용 repository 준비.

    # list: 운동 목록을 조회해 API 응답 형식(ExerciseListResponse)으로 만들어 반환.
    #   user        = 로그인한 사용자(평균 점수를 누구 기준으로 낼지)
    #   active_only = 노출 중인 운동만 볼지 여부
    #   -> ExerciseListResponse: 이 함수가 돌려주는 값의 타입(반환 타입 힌트).
    async def list(self, user: User, active_only: bool = True) -> ExerciseListResponse:
        # repository에 실제 조회를 위임. (운동, 평균점수) 쌍들의 목록을 받는다.
        rows = await self.repo.list(user.id, active_only)
        # 받은 쌍들을 하나씩 꺼내(아래 for) 응답 형식 ExerciseSummary로 변환해 리스트에 담는다.
        items = [
            ExerciseSummary(
                id=exercise.id,                       # DB 모델의 값을 응답 스키마 필드로 옮긴다.
                name_ko=exercise.name_ko,
                name_en=exercise.name_en,
                exercise_type=exercise.exercise_type,
                is_active=exercise.is_active,
                user_avg_score=user_avg_score,        # 서브쿼리로 계산된 평균(없으면 None).
            )
            for exercise, user_avg_score in rows      # rows의 각 (운동, 평균) 쌍을 풀어서 반복.
        ]
        # 변환된 요약 리스트를 최종 응답 객체에 담아 반환. (router가 이걸 camelCase JSON으로 내보낸다.)
        return ExerciseListResponse(items=items)
