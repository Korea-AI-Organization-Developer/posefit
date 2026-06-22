#!/usr/bin/env bash
# 컨테이너 기동 — DB 마이그레이션 적용 후 API 서버 실행.
# (DB 준비 대기는 compose 의 depends_on: service_healthy 로 보장)
set -e

echo "[entrypoint] alembic upgrade head ..."
alembic upgrade head

echo "[entrypoint] starting uvicorn on 0.0.0.0:8000 ..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
