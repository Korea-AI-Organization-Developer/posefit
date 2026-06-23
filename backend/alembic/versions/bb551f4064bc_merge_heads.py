"""merge_heads

Revision ID: bb551f4064bc
Revises: 8af74444c123, af722d07a0af
Create Date: 2026-06-23 15:38:45.205373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb551f4064bc'
down_revision: Union[str, Sequence[str], None] = ('8af74444c123', 'af722d07a0af')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
