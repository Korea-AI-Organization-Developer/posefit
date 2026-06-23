"""merge json_url and face_embeddings heads

Revision ID: 6b3ad77cded5
Revises: 888995dbe4d5, c4ac243616fb
Create Date: 2026-06-22 17:53:30.156019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b3ad77cded5'
down_revision: Union[str, Sequence[str], None] = ('888995dbe4d5', 'c4ac243616fb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
