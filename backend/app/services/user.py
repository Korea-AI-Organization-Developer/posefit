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
    SocialAccountRead,
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
        if not (req.tos_agreed and req.privacy_agreed):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="필수 약관(서비스·개인정보)에 모두 동의해야 합니다 (AGREEMENT_REQUIRED)",
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

    # ─── 소셜 계정 ───
    async def list_social_accounts(self, user_id: int) -> list[SocialAccountRead]:
        accounts = await self.repo.list_social_accounts(user_id)
        return [
            SocialAccountRead(
                provider=a.provider,
                provider_uid=a.provider_uid,
                provider_email=a.provider_email,
                linked_at=a.created_at,
            )
            for a in accounts
        ]

    async def link_social_account(
        self, user_id: int, provider: str, code: str, redirect_uri: str
    ) -> SocialAccountRead:
        from app.services.auth import SUPPORTED_PROVIDERS, exchange_google_code

        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 provider: {provider}")

        try:
            userinfo = await exchange_google_code(code, redirect_uri)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="소셜 코드 교환에 실패했습니다") from exc

        uid = userinfo["sub"]
        email = userinfo.get("email")
        picture = userinfo.get("picture")

        taken = await self.repo.get_social_account(provider, uid)
        if taken is not None and taken.user_id != user_id:
            raise HTTPException(status_code=409, detail="이미 다른 계정에 연결된 소셜 계정입니다")
        if taken is not None and taken.user_id == user_id:
            raise HTTPException(status_code=409, detail="이미 연동된 구글 계정입니다")

        account = await self.repo.create_social_account(user_id, provider, uid, email, picture)
        await self.db.commit()
        await self.db.refresh(account)
        return SocialAccountRead(
            provider=account.provider,
            provider_uid=account.provider_uid,
            provider_email=account.provider_email,
            linked_at=account.created_at,
        )

    async def unlink_social_account(self, user_id: int, provider: str, provider_uid: str) -> None:
        accounts = await self.repo.list_social_accounts(user_id)
        if len(accounts) <= 1:
            raise HTTPException(
                status_code=409,
                detail="마지막 소셜 계정은 해제할 수 없습니다",
            )
        account = await self.repo.get_social_account(provider, provider_uid)
        if account is None or account.user_id != user_id:
            raise HTTPException(status_code=404, detail="연결된 소셜 계정이 없습니다")
        await self.repo.delete_social_account(account)
        await self.db.commit()
