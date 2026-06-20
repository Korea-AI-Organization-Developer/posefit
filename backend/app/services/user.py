from datetime import datetime

from app.models.mixins import KST

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserStatus
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import (
    AgreementCreateRequest,
    AgreementRead,
    RegistrationStep,
    UserDetailRead,
    UserDetailUpsertRequest,
    UserRead,
)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    # ─── 조회 ───
    async def get_me(self, user_id: int) -> UserRead:
        user = await self.repo.get_with_relations(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        latest_agreement = await self.repo.get_latest_agreement(user_id)
        return self._to_read(user, latest_agreement)

    def _to_read(self, user: User, latest_agreement) -> UserRead:
        # 대표(최초 연동) 소셜 계정에서 email·avatar derive
        rep = min(user.social_accounts, key=lambda s: s.id, default=None)

        has_agreement = bool(
            latest_agreement
            and latest_agreement.tos_agreed
            and latest_agreement.privacy_agreed
            and latest_agreement.biometric_agreed
        )
        if not has_agreement:
            step = RegistrationStep.agreements_required
        elif user.detail is None:
            step = RegistrationStep.detail_required
        else:
            step = RegistrationStep.complete

        return UserRead(
            id=user.id,
            email=rep.provider_email if rep else None,
            avatar_url=rep.provider_avatar_url if rep else None,
            nickname=user.nickname,
            role=user.role.value,
            status=user.status.value,
            registration_step=step,
            detail=UserDetailRead.model_validate(user.detail) if user.detail else None,
            created_at=user.created_at,
        )

    async def get_latest_agreement(self, user_id: int) -> AgreementRead:
        agreement = await self.repo.get_latest_agreement(user_id)
        if agreement is None:
            raise HTTPException(status_code=404, detail="동의 이력이 없습니다")
        return AgreementRead.model_validate(agreement)

    # ─── 변경 ───
    async def update_nickname(self, user_id: int, nickname: str) -> UserRead:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        user.nickname = nickname
        await self.db.commit()
        return await self.get_me(user_id)

    async def withdraw(self, user_id: int) -> None:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        user.status = UserStatus.withdrawn
        user.withdrawn_at = datetime.now(KST)
        await self.db.commit()

    async def submit_agreements(
        self, user_id: int, req: AgreementCreateRequest
    ) -> AgreementRead:
        if not (req.tos_agreed and req.privacy_agreed and req.biometric_agreed):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="필수 약관(서비스·개인정보·바이오정보)에 모두 동의해야 합니다 (AGREEMENT_REQUIRED)",
            )
        agreement = await self.repo.create_agreement(
            user_id,
            req.tos_agreed,
            req.privacy_agreed,
            req.biometric_agreed,
            req.marketing_agreed,
        )
        await self.db.commit()
        await self.db.refresh(agreement)
        return AgreementRead.model_validate(agreement)

    async def upsert_detail(
        self, user_id: int, req: UserDetailUpsertRequest
    ) -> UserDetailRead:
        detail = await self.repo.get_detail(user_id)
        if detail is None:
            detail = await self.repo.create_user_detail(
                user_id, req.birthdate, req.gender, req.height, req.weight
            )
        else:
            detail.birthdate = req.birthdate
            detail.gender = req.gender
            detail.height = req.height
            detail.weight = req.weight
        await self.db.commit()
        await self.db.refresh(detail)
        return UserDetailRead.model_validate(detail)

