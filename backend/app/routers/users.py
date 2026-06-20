from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import AuthSocialCallbackRequest
from app.schemas.user import (
    AgreementCreateRequest,
    AgreementRead,
    FaceDetectResponse,
    FaceRegistrationResponse,
    SocialAccountRead,
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
@router.post("/face/detect", response_model=FaceDetectResponse)
async def detect_face(
    image: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    """웹캠 프레임에 얼굴이 정확히 1개 있는지 빠르게 확인 — 임베딩 추출 없음."""
    from ai.face.face_recognizer import count_faces

    image_bytes = await image.read()
    return FaceDetectResponse(detected=count_faces(image_bytes) == 1)


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


# ─── 소셜 계정 ───
@router.get("/social-accounts", response_model=list[SocialAccountRead])
async def list_social_accounts(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await UserService(db).list_social_accounts(user.id)


@router.post(
    "/social-accounts/{provider}:link",
    response_model=SocialAccountRead,
    status_code=status.HTTP_201_CREATED,
)
async def link_social_account(
    provider: str,
    body: AuthSocialCallbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).link_social_account(user.id, provider, body.code, body.redirect_uri)


@router.delete("/social-accounts/{provider}/{provider_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_social_account(
    provider: str,
    provider_uid: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await UserService(db).unlink_social_account(user.id, provider, provider_uid)
