"""merge_duplicate_heads

Revision ID: 8af74444c123
Revises: 6b3ad77cded5, d401afa8aeef
Create Date: 2026-06-23 10:50:22.327380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8af74444c123'
down_revision: Union[str, Sequence[str], None] = ('6b3ad77cded5', 'd401afa8aeef')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
