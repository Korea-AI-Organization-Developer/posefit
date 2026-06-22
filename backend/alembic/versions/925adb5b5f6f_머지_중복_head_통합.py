"""머지: 중복 head 통합

Revision ID: 925adb5b5f6f
Revises: 4d3a1df23c85, d5cd851cf320
Create Date: 2026-06-22 11:20:21.932304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '925adb5b5f6f'
down_revision: Union[str, Sequence[str], None] = ('4d3a1df23c85', 'd5cd851cf320')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
