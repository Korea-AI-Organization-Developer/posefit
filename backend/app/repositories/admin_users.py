from sqlalchemy import Row, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import AdminAuditLog
from app.models.enums import UserStatus
from app.models.user import Agreement, FaceEmbedding, SocialAccount, User, UserDetail
from app.models.workout import WorkoutSession


class AdminUsersRepository:
    """DB 접근만 담당 — commit 하지 않는다(트랜잭션은 service)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(
        self,
        query: str | None,
        status: UserStatus | None,
        page: int,
        size: int,
    ) -> tuple[list[Row], int]:
        # 대표 이메일: social_accounts 중 id 가 가장 작은 행의 provider_email
        email_sq = (
            select(SocialAccount.provider_email)
            .where(SocialAccount.user_id == User.id)
            .order_by(SocialAccount.id)
            .limit(1)
            .correlate(User)
            .scalar_subquery()
        )

        base = select(User, email_sq.label("email"))

        if status is not None:
            base = base.where(User.status == status)

        if query is not None:
            email_match = exists(
                select(SocialAccount.id).where(
                    SocialAccount.user_id == User.id,
                    SocialAccount.provider_email.ilike(f"%{query}%"),
                )
            )
            base = base.where(
                or_(
                    User.nickname.ilike(f"%{query}%"),
                    email_match,
                )
            )

        total: int = (
            await self.db.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()

        rows = (
            await self.db.execute(
                base.order_by(User.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).all()

        return rows, total

    async def get_user_detail(self, user_id: int) -> tuple[User, str | None, int] | None:
        user = (
            await self.db.execute(
                select(User)
                .where(User.id == user_id)
                .options(
                    selectinload(User.detail),
                    selectinload(User.face_embedding),
                    selectinload(User.agreement),
                    selectinload(User.social_accounts),
                )
            )
        ).scalar_one_or_none()

        if user is None:
            return None

        email: str | None = (
            await self.db.execute(
                select(SocialAccount.provider_email)
                .where(SocialAccount.user_id == user_id)
                .order_by(SocialAccount.id)
                .limit(1)
            )
        ).scalar_one_or_none()

        session_count: int = (
            await self.db.execute(
                select(func.count()).where(WorkoutSession.user_id == user_id)
            )
        ).scalar_one()

        return user, email, session_count

    async def get_user_by_id(self, user_id: int) -> User | None:
        return (
            await self.db.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none()

    async def create_audit_log(
        self,
        admin_id: int,
        action: str,
        target_type: str,
        target_id: str,
        detail: dict,
        ip_address: str | None,
    ) -> None:
        self.db.add(
            AdminAuditLog(
                admin_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
                ip_address=ip_address,
            )
        )
