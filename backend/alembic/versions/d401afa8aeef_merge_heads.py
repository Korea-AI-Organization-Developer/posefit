"""merge heads

Revision ID: d401afa8aeef
Revises: 888995dbe4d5, c4ac243616fb
Create Date: 2026-06-22 19:13:40.278743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd401afa8aeef'
down_revision: Union[str, Sequence[str], None] = ('888995dbe4d5', 'c4ac243616fb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
