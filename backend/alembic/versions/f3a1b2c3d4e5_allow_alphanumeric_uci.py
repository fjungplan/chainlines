"""allow_alphanumeric_uci

Revision ID: f3a1b2c3d4e5
Revises: efc94c85dbe0
Create Date: 2026-01-16 10:30:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a1b2c3d4e5'
down_revision = '87a6d628ebda'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop strict A-Z constraint
    op.drop_constraint('check_uci_code_format', 'team_era', type_='check')
    
    # Create new constraint allowing A-Z and 0-9
    op.create_check_constraint(
        'check_uci_code_format',
        'team_era',
        "uci_code IS NULL OR uci_code ~ '^[A-Z0-9]{3}$'"
    )


def downgrade() -> None:
    # Revert to strict A-Z
    # Note: potentially dangerous if data exists that violates this
    op.drop_constraint('check_uci_code_format', 'team_era', type_='check')
    
    op.create_check_constraint(
        'check_uci_code_format',
        'team_era',
        "uci_code IS NULL OR uci_code ~ '^[A-Z]{3}$'"
    )
