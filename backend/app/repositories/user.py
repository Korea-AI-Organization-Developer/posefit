from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import (
    Agreement,
    SocialAccount,
    User,
    UserDetail,
)


class UserRepository:
    """DB 접근만 담당 — commit 하지 않는다(트랜잭션은 service)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── User ───
    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_with_relations(self, user_id: int) -> User | None:
        """registrationStep·email·avatar 계산에 필요한 1:N/1:1 관계를 eager-load."""
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.social_accounts),
                selectinload(User.detail),
            )
        )
        return result.scalar_one_or_none()

    async def find_by_social(self, provider: str, provider_uid: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .join(SocialAccount, SocialAccount.user_id == User.id)
            .where(
                SocialAccount.provider == provider,
                SocialAccount.provider_uid == provider_uid,
            )
        )
        return result.scalar_one_or_none()

    async def create_user(self, nickname: str) -> User:
        user = User(nickname=nickname)
        self.db.add(user)
        await self.db.flush()  # id 확보 (commit 은 service)
        return user

    # ─── Social account ───
    async def get_social_account(
        self, provider: str, provider_uid: str
    ) -> SocialAccount | None:
        result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.provider == provider,
                SocialAccount.provider_uid == provider_uid,
            )
        )
        return result.scalar_one_or_none()

    async def create_social_account(
        self,
        user_id: int,
        provider: str,
        provider_uid: str,
        provider_email: str | None,
        provider_avatar_url: str | None = None,
    ) -> SocialAccount:
        account = SocialAccount(
            user_id=user_id,
            provider=provider,
            provider_uid=provider_uid,
            provider_email=provider_email,
            provider_avatar_url=provider_avatar_url,
        )
        self.db.add(account)
        return account

    async def list_social_accounts(self, user_id: int) -> list[SocialAccount]:
        result = await self.db.execute(
            select(SocialAccount)
            .where(SocialAccount.user_id == user_id)
            .order_by(SocialAccount.id)
        )
        return list(result.scalars().all())

    async def get_social_account_by_provider(
        self, user_id: int, provider: str
    ) -> SocialAccount | None:
        result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def delete_social_account(self, account: SocialAccount) -> None:
        await self.db.delete(account)

    # ─── Agreement (append-only) ───
    async def get_latest_agreement(self, user_id: int) -> Agreement | None:
        result = await self.db.execute(
            select(Agreement)
            .where(Agreement.user_id == user_id)
            .order_by(Agreement.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_agreement(
        self,
        user_id: int,
        tos: bool,
        privacy: bool,
        marketing: bool,
    ) -> Agreement:
        agreement = Agreement(
            user_id=user_id,
            tos_agreed=tos,
            privacy_agreed=privacy,
            marketing_agreed=marketing,
        )
        self.db.add(agreement)
        await self.db.flush()
        return agreement

    # ─── UserDetail (1:1 upsert) ───
    async def get_detail(self, user_id: int) -> UserDetail | None:
        result = await self.db.execute(
            select(UserDetail).where(UserDetail.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user_detail(
        self,
        user_id: int,
        birthdate,
        gender,
        height: float | None,
        weight: float | None,
    ) -> UserDetail:
        detail = UserDetail(
            user_id=user_id,
            birthdate=birthdate,
            gender=gender,
            height=height,
            weight=weight,
        )
        self.db.add(detail)
        return detail

