"""relax_prominence_constraint_allow_zero

Revision ID: e27b98562d8f
Revises: aeaaf6988cb7
Create Date: 2026-01-04 15:48:11.347360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e27b98562d8f'
down_revision: Union[str, None] = 'aeaaf6988cb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old constraint
    op.drop_constraint('check_prominence_range', 'team_sponsor_link', type_='check')
    # Add new constraint allowing 0
    op.create_check_constraint(
        'check_prominence_range',
        'team_sponsor_link',
        'prominence_percent >= 0 AND prominence_percent <= 100'
    )


def downgrade() -> None:
    op.drop_constraint('check_prominence_range', 'team_sponsor_link', type_='check')
    op.create_check_constraint(
        'check_prominence_range',
        'team_sponsor_link',
        'prominence_percent > 0 AND prominence_percent <= 100'
    )
