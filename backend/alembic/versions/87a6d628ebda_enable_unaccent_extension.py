"""enable unaccent extension

Revision ID: 87a6d628ebda
Revises: d8243ac55282
Create Date: 2026-01-15 09:16:08.366817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87a6d628ebda'
down_revision: Union[str, None] = 'd8243ac55282'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply database schema changes."""
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    """Revert database schema changes.
    
    WARNING: Make sure this migration is reversible!
    Consider data loss implications before rolling back.
    """
    op.execute("DROP EXTENSION IF EXISTS unaccent")
