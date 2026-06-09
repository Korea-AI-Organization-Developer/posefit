from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Agreement, SocialAccount, User, UserDetail


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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
        await self.db.flush()  # id 확보 (commit은 service에서)
        return user

    async def create_social_account(
        self,
        user_id: int,
        provider: str,
        provider_uid: str,
        provider_email: str | None,
    ) -> SocialAccount:
        account = SocialAccount(
            user_id=user_id,
            provider=provider,
            provider_uid=provider_uid,
            provider_email=provider_email,
        )
        self.db.add(account)
        return account

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

    async def create_agreement(
        self,
        user_id: int,
        tos: bool,
        privacy: bool,
        biometric: bool,
        marketing: bool,
    ) -> Agreement:
        agreement = Agreement(
            user_id=user_id,
            tos_agreed=tos,
            privacy_agreed=privacy,
            biometric_agreed=biometric,
            marketing_agreed=marketing,
        )
        self.db.add(agreement)
        return agreement

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
