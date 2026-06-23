# APIRouter: 엔드포인트 묶음. Depends: 의존성 주입(DB 세션·로그인 사용자). HTTPException: 에러 응답.
from fastapi import APIRouter, Depends, HTTPException
# AsyncSession: DB 비동기 연결(세션) 타입.
from sqlalchemy.ext.asyncio import AsyncSession

# get_db: 요청마다 DB 세션을 열어주는 함수. get_current_user: 토큰을 해독해 로그인 사용자를 알려준다.
from app.database import get_db
from app.dependencies import get_current_user
# User: 로그인 사용자 모델.
from app.models.user import User
# FeedbackRead: 세트 피드백 응답 형식. 종합(:summary) 요청/응답 스키마도 함께 가져온다.
from app.schemas.feedback import (
    ExerciseFeedbackSummaryRequest,
    ExerciseFeedbackSummaryResponse,
    FeedbackRead,
)
# FeedbackService: 세트 피드백 조회 + LangGraph 종합 로직.
from app.services.feedback import FeedbackService

# exercise 라우터와 같은 prefix("/exercises")를 쓰되, 문서 분류는 Feedbacks 태그로 둔다.
router = APIRouter(prefix="/exercises", tags=["Feedbacks"])


# GET /exercises/{exercise_id}/feedbacks — 지정 종목의 오늘(KST) 피드백을 id ASC 로 조회.
#   라우터는 얇게: 입력을 받아 service 를 호출하고, 종목이 없으면 404 로 바꿔준다.
@router.get("/{exercise_id}/feedbacks", response_model=list[FeedbackRead])
async def list_exercise_feedbacks(
    exercise_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await FeedbackService(db).list_today(user, exercise_id)
    if result is None:
        raise HTTPException(status_code=404, detail="운동 종목을 찾을 수 없습니다.")
    return result


# POST /exercises/{exercise_id}/feedbacks:summary — 운동 종합 피드백 생성(미저장).
#   본문 sessionIds(이번 묶음 세트 세션) 의 피드백을 모아 LLM 으로 1건으로 합쳐 반환한다.
@router.post("/{exercise_id}/feedbacks:summary", response_model=ExerciseFeedbackSummaryResponse)
async def summarize_exercise_feedbacks(
    exercise_id: int,
    body: ExerciseFeedbackSummaryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await FeedbackService(db).summarize(user, exercise_id, body.session_ids)
    if result is None:
        raise HTTPException(status_code=404, detail="운동 종목을 찾을 수 없습니다.")
    return result
