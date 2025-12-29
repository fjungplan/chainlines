"""merge heads

Revision ID: aeaaf6988cb7
Revises: 36e7d6258a25, a1b2c3d4e5f6
Create Date: 2025-12-29 13:35:58.844272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aeaaf6988cb7'
down_revision: Union[str, None] = ('36e7d6258a25', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply database schema changes."""
    pass


def downgrade() -> None:
    """Revert database schema changes.
    
    WARNING: Make sure this migration is reversible!
    Consider data loss implications before rolling back.
    """
    pass
