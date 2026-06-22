#!/usr/bin/env bash
# 컨테이너 기동 — DB 마이그레이션 적용 후 API 서버 실행.
# healthcheck 통과 후에도 MySQL 유저/DB 초기화가 완료되지 않을 수 있으므로
# alembic 실행 전 실제 접속 가능 여부를 재시도한다.
set -e

echo "[entrypoint] waiting for MySQL to accept connections ..."
until python -c "
import asyncio, os
import aiomysql
url = os.environ['DATABASE_URL'].replace('mysql+aiomysql://', '')
user, rest = url.split(':', 1)
pw, rest2 = rest.split('@', 1)
host, rest3 = rest2.split(':', 1)
port_db = rest3.split('/', 1)
port = int(port_db[0])
db = port_db[1]
async def check():
    conn = await aiomysql.connect(host=host, port=port, user=user, password=pw, db=db)
    conn.close()
asyncio.run(check())
" 2>/dev/null; do
  echo "[entrypoint] MySQL not ready yet, retrying in 3s ..."
  sleep 3
done

echo "[entrypoint] alembic upgrade head ..."
alembic upgrade head

echo "[entrypoint] starting uvicorn on 0.0.0.0:8000 ..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
