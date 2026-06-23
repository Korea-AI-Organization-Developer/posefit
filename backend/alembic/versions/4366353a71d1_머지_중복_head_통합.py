"""머지: 중복 head 통합

Revision ID: 4366353a71d1
Revises: 6b3ad77cded5, d401afa8aeef
Create Date: 2026-06-23 11:35:14.216981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4366353a71d1'
down_revision: Union[str, Sequence[str], None] = ('6b3ad77cded5', 'd401afa8aeef')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
