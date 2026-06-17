"""머지: 복수 head 통합

Revision ID: d5cd851cf320
Revises: 3a6ba87840b6, 7a492208e919
Create Date: 2026-06-17 10:02:14.502051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5cd851cf320'
down_revision: Union[str, Sequence[str], None] = ('3a6ba87840b6', '7a492208e919')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
