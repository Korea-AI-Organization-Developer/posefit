from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    AgreementCreateRequest,
    AgreementRead,
    FaceRegistrationResponse,
    UserDetailRead,
    UserDetailUpsertRequest,
    UserRead,
    UserUpdateRequest,
)
from app.services.user import UserService

router = APIRouter(prefix="/users/me", tags=["Users"])


# ─── 프로필 ───
@router.get("", response_model=UserRead)
async def get_me(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await UserService(db).get_me(user.id)


@router.patch("", response_model=UserRead)
async def update_me(
    body: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).update_nickname(user.id, body.nickname)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_me(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await UserService(db).withdraw(user.id)


# ─── 약관 (가입 1단계 / 설정 동의 변경) ───
@router.get("/agreements", response_model=AgreementRead)
async def get_my_agreements(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await UserService(db).get_latest_agreement(user.id)


@router.post(
    "/agreements", response_model=AgreementRead, status_code=status.HTTP_201_CREATED
)
async def submit_agreements(
    body: AgreementCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).submit_agreements(user.id, body)


# ─── 신체 정보 (가입 2단계 / 설정) ───
@router.put("/detail", response_model=UserDetailRead)
async def upsert_my_detail(
    body: UserDetailUpsertRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).upsert_detail(user.id, body)


# ─── 얼굴 (가입 3단계 / 설정) ───
@router.post(
    "/face", response_model=FaceRegistrationResponse, status_code=status.HTTP_201_CREATED
)
async def register_face(
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).register_face(
        user.id, await image.read(), replace=False
    )


@router.put("/face", response_model=FaceRegistrationResponse)
async def replace_face(
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).register_face(
        user.id, await image.read(), replace=True
    )


@router.delete("/face", status_code=status.HTTP_204_NO_CONTENT)
async def delete_face(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await UserService(db).delete_face(user.id)
