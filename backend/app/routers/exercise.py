# APIRouter: 관련된 엔드포인트(주소)들을 한 묶음으로 만드는 도구.
# Depends: "의존성 주입". 함수 실행 전에 필요한 것(DB 세션, 로그인 사용자)을 FastAPI가 자동으로 만들어 넣어줌.
# Query: 쿼리 파라미터(주소 뒤 ?key=value)를 받겠다고 표시하는 도구.
from fastapi import APIRouter, Depends, Query
# AsyncSession: DB 비동기 연결(세션) 타입.
from sqlalchemy.ext.asyncio import AsyncSession

# get_db: 요청마다 DB 세션을 새로 열어주는 함수(database.py). Depends와 함께 쓴다.
from app.database import get_db
# get_current_user: 요청 헤더의 로그인 토큰을 해독해 "지금 누가 요청했는지"(User)를 알려주는 함수.
from app.dependencies import get_current_user
# User: 로그인 사용자 모델.
from app.models.user import User
# ExerciseListResponse: 이 엔드포인트의 응답 형식(스키마).
from app.schemas.exercise import ExerciseListResponse
# ExerciseService: 실제 로직을 담당하는 service 층.
from app.services.exercise import ExerciseService

# 이 파일의 모든 주소는 "/exercises"로 시작한다(prefix). tags는 자동 문서(/docs)에서의 분류 이름.
router = APIRouter(prefix="/exercises", tags=["Exercises"])


# @router.get(""): 이 함수가 GET 요청을 처리한다는 표시. prefix와 합쳐져 최종 경로는 GET /exercises.
# response_model: 응답을 이 스키마로 검증·직렬화(=camelCase JSON으로 변환)하라는 지정.
@router.get("", response_model=ExerciseListResponse)
async def list_exercises(
    # active_only: ?activeOnly=true 같은 쿼리 파라미터로 받는다.
    #   default=True   → 안 주면 기본값 True(노출 운동만)
    #   alias="activeOnly" → 주소에서는 camelCase(activeOnly), 파이썬 변수는 snake_case(active_only)
    active_only: bool = Query(default=True, alias="activeOnly"),
    # user: get_current_user가 토큰을 해독해 자동으로 채워 넣어준다. "본인 평균"을 내려면 누구인지 필요.
    user: User = Depends(get_current_user),
    # db: get_db가 이 요청용 DB 세션을 자동으로 열어 넣어준다.
    db: AsyncSession = Depends(get_db),
):
    # router는 "얇게": 직접 로직을 짜지 않고 service를 만들어 호출만 한다. 그 결과가 그대로 응답이 된다.
    return await ExerciseService(db).list(user, active_only)
