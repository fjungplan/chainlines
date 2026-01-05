"""add_metadata_fields_to_scraper_run

Revision ID: bb50b382938a
Revises: 3a35478ed066
Create Date: 2026-01-04 22:25:32.777941

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb50b382938a'
down_revision: Union[str, None] = '3a35478ed066'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply database schema changes."""
    # Add dry_run column with server default
    op.add_column('scraper_runs', sa.Column('dry_run', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    """Revert database schema changes."""
    op.drop_column('scraper_runs', 'dry_run')
