"""exercises_is_active_기본값_비활성화로_변경

Revision ID: 4d3a1df23c85
Revises: 6286cafa5581
Create Date: 2026-06-18 13:38:33.571935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d3a1df23c85'
down_revision: Union[str, Sequence[str], None] = '6286cafa5581'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "exercises",
        "is_active",
        existing_type=sa.Boolean(),
        server_default=sa.text("0"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "exercises",
        "is_active",
        existing_type=sa.Boolean(),
        server_default=sa.text("1"),
        existing_nullable=False,
    )
