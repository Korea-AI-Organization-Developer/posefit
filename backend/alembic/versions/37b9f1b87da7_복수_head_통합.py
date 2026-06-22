"""복수 head 통합

Revision ID: 37b9f1b87da7
Revises: 4d3a1df23c85, d5cd851cf320
Create Date: 2026-06-22 09:44:46.791602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37b9f1b87da7'
down_revision: Union[str, Sequence[str], None] = ('4d3a1df23c85', 'd5cd851cf320')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
