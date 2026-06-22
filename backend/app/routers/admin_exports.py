from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.admin import AdminAccount
from app.models.enums import SessionStatus
from app.schemas.admin_exports import AdminSessionPage
from app.services.admin_exports import AdminExportsService

router = APIRouter(prefix="/admin", tags=["Admin Exports"])


@router.get("/workout-sessions", response_model=AdminSessionPage)
async def list_workout_sessions(
    status: SessionStatus | None = Query(default=None),
    exercise_id: int | None = Query(default=None, alias="exerciseId"),
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminExportsService(db).list_sessions(
        status, exercise_id, from_dt, to_dt, page, size
    )


@router.get("/exports/keypoints")
async def export_keypoints(
    request: Request,
    session_id: int | None = Query(default=None, alias="sessionId"),
    exercise_id: int | None = Query(default=None, alias="exerciseId"),
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    fmt: str = Query(default="jsonl", alias="format", pattern="^(jsonl|json)$"),
    admin: AdminAccount = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if fmt == "json" and session_id is None:
        raise HTTPException(status_code=400, detail="format=json 은 sessionId 가 필요합니다")

    ip = request.client.host if request.client else None
    service = AdminExportsService(db)

    if fmt == "json":
        content, filename = await service.export_json(session_id, admin.id, ip)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    lines, filename = await service.export_jsonl(
        session_id, exercise_id, from_dt, to_dt, admin.id, ip
    )

    def generate():
        for line in lines:
            yield line + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
