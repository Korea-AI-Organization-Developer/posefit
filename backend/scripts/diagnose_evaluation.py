"""
리포트 종합평가가 'AI' 대신 '규칙 기반(기본 내용)'으로 나오는 원인을 진단한다.

사용법:
  cd backend
  uv run python scripts/diagnose_evaluation.py --user-id 1

_try_ai_evaluation 이 None(→ 규칙 기반 폴백) 을 반환하는 5가지 조건을 순서대로 점검한다.
"""

import argparse
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.database import AsyncSessionLocal
from app.repositories.feedback import FeedbackRepository
from app.repositories.user import UserRepository
from app.repositories.workout_analysis import WorkoutAnalysisRepository
from app.services.report import ReportService
from app.schemas.report import ReportPeriod


async def _probe_raw_llm(api_key: str) -> None:
    """그래프 노드가 삼킨 LLM 에러를 직접 호출로 드러낸다."""
    from langchain_core.messages import HumanMessage
    from langchain_google_genai import ChatGoogleGenerativeAI

    def _call():
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model, api_key=api_key, temperature=0.4, thinking_budget=0
            )
        except Exception:
            llm = ChatGoogleGenerativeAI(model=settings.gemini_model, api_key=api_key, temperature=0.4)
        return llm.invoke([HumanMessage(content="안녕이라고만 답해")])

    t = time.time()
    try:
        r = await asyncio.to_thread(_call)
        print(f"       ✅ raw 호출 성공 ({round(time.time() - t, 1)}초): {str(r.content)[:40]}")
        print("       → LLM 자체는 정상. 그래프/타임아웃 쪽 문제일 수 있음")
    except Exception as exc:  # noqa: BLE001
        print(f"       ❌ raw 호출 실패 ({round(time.time() - t, 1)}초):")
        print(f"          {str(exc)[:400]}")


async def main(user_id: int) -> None:
    async with AsyncSessionLocal() as db:
        svc = ReportService(db)
        print("=" * 60)
        print(f" 종합평가 진단 (user_id={user_id})")
        print("=" * 60)

        # 0) 유저 존재
        user = await UserRepository(db).get_by_id(user_id)
        if user is None:
            print("❌ [0] 해당 user_id 가 DB에 없음")
            return
        print(f"✅ [0] 유저 존재 (가입일 {user.created_at.date()})")

        ucd = user.created_at.date()
        summary = await svc.get_summary(user_id, ReportPeriod.cumulative, None, None, ucd)

        # 1) 세션 수
        if summary.sessions_count == 0:
            print("❌ [1] 누적 세션 수 0 → 규칙 기반 폴백")
            print("     원인: workout_daily_stats 에 이 유저 데이터 없음")
            return
        print(f"✅ [1] 누적 세션 수 {summary.sessions_count}회")

        # 2) 피드백/분석 데이터
        fb = await FeedbackRepository(db).list_recent_contents(user_id, None, 60)
        ar = await WorkoutAnalysisRepository(db).list_recent_results(user_id, None, 30)
        print(f"     피드백 {len(fb)}개 / 분석결과 {len(ar)}개")
        if not fb and not ar:
            print("❌ [2] 피드백·분석결과 둘 다 없음 → 규칙 기반 폴백")
            print("     원인: 운동 세션이 종료(stop)된 적 없어 feedbacks/workout_analyses 가 빔")
            return
        print("✅ [2] LLM 입력 데이터 있음")

        # 3) API 키
        api_key = settings.google_api_key or settings.gemini_api_key
        if not api_key:
            print("❌ [3] API 키 없음 (.env GOOGLE_API_KEY/GEMINI_API_KEY 비어있음) → 규칙 기반 폴백")
            return
        print(f"✅ [3] API 키 있음 ({api_key[:4]}…, {len(api_key)}자) | 모델={settings.gemini_model}")

        # 4) 실제 LLM 호출 (그래프 long_term)
        print("⏳ [4] LangGraph long_term 직접 호출 중...")
        t = time.time()
        try:
            result = await asyncio.to_thread(
                ReportService._run_long_term_graph,
                fb, ar,
                {"sessions_count": summary.sessions_count, "avg_score": None, "best_exercise": None},
                api_key, settings.gemini_model,
            )
            dt = round(time.time() - t, 1)
            if result and result.get("messages"):
                print(f"✅ [4] LLM 정상 응답 ({dt}초, 메시지 {len(result['messages'])}개)")
                print("     → AI 종합평가 정상 동작 가능. (화면이 규칙 기반이면 서버 재시작/캐시 확인)")
            else:
                print(f"❌ [4] LLM 응답이 비어있음 ({dt}초) → 규칙 기반 폴백")
                print("     [4b] 실제 원인 확인 — raw LLM 직접 호출:")
                await _probe_raw_llm(api_key)
        except Exception as exc:  # noqa: BLE001
            dt = round(time.time() - t, 1)
            print(f"❌ [4] LLM 호출 실패 ({dt}초): {str(exc)[:300]}")
            print("     → 위 에러 메시지가 실제 원인 (429=할당량 / 404=모델명 / PERMISSION=키 등)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, default=1)
    args = parser.parse_args()
    asyncio.run(main(args.user_id))
