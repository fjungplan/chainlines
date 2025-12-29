"""Add reverted_at and reverted_by to edit_history

Revision ID: a1b2c3d4e5f6
Revises: efc94c85dbe0
Create Date: 2025-12-29 09:50:00.000000

Adds columns to track when and by whom an edit was reverted,
and updates the EditStatus enum to include REVERTED value.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'efc94c85dbe0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add reverted tracking columns to edit_history."""
    # Add reverted_by column with FK to users
    op.add_column('edit_history', sa.Column(
        'reverted_by',
        sa.UUID(),
        sa.ForeignKey('users.user_id', ondelete='SET NULL'),
        nullable=True
    ))
    
    # Add reverted_at timestamp column
    op.add_column('edit_history', sa.Column(
        'reverted_at',
        sa.TIMESTAMP(),
        nullable=True
    ))
    
    # Note: EditStatus enum update (APPLIED -> REVERTED) is handled at the
    # application level since we use native_enum=False (string storage).
    # Existing APPLIED values in DB can be migrated via data migration if needed.


def downgrade() -> None:
    """Remove reverted tracking columns from edit_history."""
    op.drop_column('edit_history', 'reverted_at')
    op.drop_column('edit_history', 'reverted_by')
