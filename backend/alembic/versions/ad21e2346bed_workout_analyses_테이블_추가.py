"""workout_analyses 테이블 추가

Revision ID: ad21e2346bed
Revises: 925adb5b5f6f
Create Date: 2026-06-22 13:09:10.089947

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import app.models.mixins

# revision identifiers, used by Alembic.
revision: str = 'ad21e2346bed'
down_revision: Union[str, Sequence[str], None] = '925adb5b5f6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'workout_analyses',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('exercise_id', sa.BigInteger(), nullable=False),
        sa.Column('overall_status', sa.String(length=30), nullable=True, comment='correct | needs_correction | unknown'),
        sa.Column('analysis_result', sa.JSON(), nullable=False, comment='pose_decide_node 출력(errors·severity·occurrence_ratio 등).'),
        sa.Column('created_at', app.models.mixins._UTCDateTime(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
        sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['workout_sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_analysis_user_exercise', 'workout_analyses', ['user_id', 'exercise_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_analysis_user_exercise', table_name='workout_analyses')
    op.drop_table('workout_analyses')
