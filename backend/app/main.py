import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import (
    admin_audit,
    admin_auth,
    admin_exercises,
    admin_exports,
    admin_llm,
    admin_stats,
    admin_users,
    auth,
    exercise,
    feedback,
    report,
    users,
    workout,
    workout_session,
)


def _warmup_report_graph() -> None:
    """리포트 종합평가 LangGraph(chromadb 포함)를 미리 import·컴파일해 둔다.
    첫 종합평가 요청이 ~9초 import 비용을 물지 않도록 한다."""
    try:
        import ai.llm.langgraph_V1  # noqa: F401 — import 시점에 그래프 컴파일됨
    except Exception as exc:  # noqa: BLE001 — 워밍업 실패는 무시(요청 시 lazy import 로 폴백)
        logging.getLogger(__name__).warning("LangGraph 워밍업 실패(무시): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 기동을 막지 않도록 백그라운드 스레드에서 그래프를 워밍업한다.
    asyncio.create_task(asyncio.to_thread(_warmup_report_graph))
    yield


app = FastAPI(title="PoseFit API", lifespan=lifespan)

_uploads_dir = Path("uploads")
_uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /api=네임스페이스, /v1=API 버전 (docs/openapi.yaml servers base path 와 일치)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
# exercise 라우터를 앱에 등록. 이 줄이 있어야 /api/v1/exercises 주소가 실제로 동작한다. ← 이번에 추가됨.
# prefix="/api/v1" + 라우터의 prefix="/exercises" 가 합쳐져 최종 경로는 /api/v1/exercises.
app.include_router(exercise.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
app.include_router(workout.router, prefix="/api/v1")
app.include_router(workout_session.router, prefix="/api/v1")
app.include_router(admin_auth.router, prefix="/api/v1")
app.include_router(admin_users.router, prefix="/api/v1")
app.include_router(admin_exercises.router, prefix="/api/v1")
app.include_router(admin_llm.router, prefix="/api/v1")
app.include_router(admin_exports.router, prefix="/api/v1")
app.include_router(admin_stats.router, prefix="/api/v1")
app.include_router(admin_audit.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
