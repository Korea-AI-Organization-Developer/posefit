from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# auth, users 에 더해 새로 만든 exercise 라우터를 함께 가져온다(import). ← 이번에 exercise 추가됨.
from app.routers import admin_auth, auth, exercise, feedback, users, workout

app = FastAPI(title="PoseFit API")

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
# feedback 라우터 등록 → GET /api/v1/exercises/{id}/feedbacks (종목별 당일 피드백 조회).
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(workout.router, prefix="/api/v1")
app.include_router(admin_auth.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
