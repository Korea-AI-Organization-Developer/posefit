"""users token_version 추가

refresh 토큰 무효화(로그아웃)를 위한 버전 컬럼. ERD 변경 최소화를 위해
별도 refresh_tokens 테이블 대신 users 에 컬럼 1개를 둔다.

Revision ID: 7c1d9e4a2b3f
Revises: 84a61b4aea76
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c1d9e4a2b3f"
down_revision: Union[str, Sequence[str], None] = "84a61b4aea76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="refresh 토큰 무효화용. 로그아웃 시 +1 → 이전에 발급된 refresh 토큰 전부 무효.",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "token_version")
