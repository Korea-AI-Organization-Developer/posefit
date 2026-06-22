# APIRouter: 엔드포인트 묶음. Depends: 의존성 주입(DB 세션·로그인 사용자). HTTPException: 에러 응답.
from fastapi import APIRouter, Depends, HTTPException
# AsyncSession: DB 비동기 연결(세션) 타입.
from sqlalchemy.ext.asyncio import AsyncSession

# get_db: 요청마다 DB 세션을 열어주는 함수. get_current_user: 토큰을 해독해 로그인 사용자를 알려준다.
from app.database import get_db
from app.dependencies import get_current_user
# User: 로그인 사용자 모델.
from app.models.user import User
# FeedbackRead: 세트 피드백 응답 형식. DailyFeedbackRead: 일일 종합 피드백 응답 형식.
from app.schemas.feedback import FeedbackRead
from app.schemas.daily_feedback import DailyFeedbackRead
# FeedbackService: 세트 피드백 조회 로직. DailyFeedbackService: 오늘 피드백을 LangGraph 로 종합.
from app.services.feedback import FeedbackService
from app.services.daily_feedback import DailyFeedbackService

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


# GET /exercises/{exercise_id}/daily-feedback — 위 목록과 같은 "오늘(KST)" 세트 피드백들을
#   LangGraph 일일 분기로 종합해 한 건의 피드백으로 돌려준다(같은 쿼리 기반이라 목록과 일관).
@router.get("/{exercise_id}/daily-feedback", response_model=DailyFeedbackRead)
async def get_exercise_daily_feedback(
    exercise_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await DailyFeedbackService(db).summarize_today(user, exercise_id)
    if result is None:
        raise HTTPException(status_code=404, detail="운동 종목을 찾을 수 없습니다.")
    return result
