"""add_scraper_status_enums

Revision ID: 3a35478ed066
Revises: ee0db4ac2d89
Create Date: 2026-01-04 21:40:44.412359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3a35478ed066'
down_revision: Union[str, None] = 'ee0db4ac2d89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply database schema changes."""
    # Add new enum values. 
    # content has to be outside of transaction block for Postgres
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE scraperrunstatus ADD VALUE IF NOT EXISTS 'PAUSED'")
        op.execute("ALTER TYPE scraperrunstatus ADD VALUE IF NOT EXISTS 'ABORTED'")


def downgrade() -> None:
    """Revert database schema changes."""
    # Removing values from enum is hard in Postgres, requires type recreation.
    # For now, we accept they exist.
    pass
