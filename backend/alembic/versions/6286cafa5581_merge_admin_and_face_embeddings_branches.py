"""merge admin and face_embeddings branches

Revision ID: 6286cafa5581
Revises: 3a6ba87840b6, 7a492208e919
Create Date: 2026-06-17 11:20:03.229634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6286cafa5581'
down_revision: Union[str, Sequence[str], None] = ('3a6ba87840b6', '7a492208e919')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
