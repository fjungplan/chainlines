"""initial_schema_migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-16 12:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("""
        CREATE TYPE user_role_enum AS ENUM (
            'EDITOR',
            'TRUSTED_EDITOR',
            'MODERATOR',
            'ADMIN'
        )
    """)
    
    op.execute("""
        CREATE TYPE edit_action_enum AS ENUM (
            'CREATE',
            'UPDATE',
            'DELETE'
        )
    """)
    
    op.execute("""
        CREATE TYPE edit_status_enum AS ENUM (
            'PENDING',
            'APPROVED',
            'REJECTED',
            'APPLIED'
        )
    """)
    
    op.execute("""
        CREATE TYPE lineage_event_type_enum AS ENUM (
            'LEGAL_TRANSFER',
            'SPIRITUAL_SUCCESSION',
            'MERGE',
            'SPLIT'
        )
    """)
    
    # Create users table
    op.create_table('users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('google_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('role', postgresql.ENUM('EDITOR', 'TRUSTED_EDITOR', 'MODERATOR', 'ADMIN', name='user_role_enum', create_type=False), nullable=False, server_default='EDITOR'),
        sa.Column('approved_edits_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('banned_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_login_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('google_id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_google_id', 'users', ['google_id'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])
    
    # Create sponsor_master table
    op.create_table('sponsor_master',
        sa.Column('master_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('legal_name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('industry_sector', sa.String(length=100), nullable=True),
        sa.Column('is_protected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['last_modified_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('master_id'),
        sa.UniqueConstraint('legal_name')
    )
    op.create_index('idx_sponsor_master_legal_name', 'sponsor_master', ['legal_name'])
    op.create_index('idx_sponsor_master_protected', 'sponsor_master', ['is_protected'])
    
    # Create sponsor_brand table
    op.create_table('sponsor_brand',
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('master_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('brand_name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('default_hex_color', sa.String(length=7), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['last_modified_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['master_id'], ['sponsor_master.master_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('brand_id'),
        sa.UniqueConstraint('master_id', 'brand_name', name='uq_master_brand')
    )
    op.create_index('idx_sponsor_brand_master_id', 'sponsor_brand', ['master_id'])
    
    # Create team_node table
    op.create_table('team_node',
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('legal_name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('founding_year', sa.Integer(), nullable=False),
        sa.Column('dissolution_year', sa.Integer(), nullable=True),
        sa.Column('owned_by_sponsor_master_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_protected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('latest_team_name', sa.String(length=255), nullable=True),
        sa.Column('latest_uci_code', sa.String(length=3), nullable=True),
        sa.Column('current_tier', sa.Integer(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('current_tier IN (1, 2, 3)', name='check_current_tier'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['last_modified_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owned_by_sponsor_master_id'], ['sponsor_master.master_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('node_id'),
        sa.UniqueConstraint('legal_name')
    )
    
    # Add computed column is_active
    op.execute("""
        ALTER TABLE team_node ADD COLUMN is_active BOOLEAN 
        GENERATED ALWAYS AS (dissolution_year IS NULL) STORED
    """)
    
    op.create_index('idx_team_node_legal_name', 'team_node', ['legal_name'])
    op.create_index('idx_team_node_founding_year', 'team_node', ['founding_year'])
    op.create_index('idx_team_node_dissolution_year', 'team_node', ['dissolution_year'])
    op.create_index('idx_team_node_is_active', 'team_node', ['is_active'])
    
    # Create team_era table
    op.create_table('team_era',
        sa.Column('era_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('season_year', sa.Integer(), nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('registered_name', sa.String(length=255), nullable=False),
        sa.Column('uci_code', sa.String(length=3), nullable=True),
        sa.Column('is_name_auto_generated', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_manual_override', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_auto_filled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tier_level', sa.Integer(), nullable=True),
        sa.Column('has_license', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('source_origin', sa.String(length=50), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('tier_level IN (1, 2, 3)', name='check_tier_level'),
        sa.CheckConstraint("uci_code IS NULL OR uci_code ~ '^[A-Z]{3}$'", name='check_uci_code_format'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['last_modified_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['node_id'], ['team_node.node_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('era_id'),
        sa.UniqueConstraint('node_id', 'season_year', 'valid_from', name='uq_node_year_period')
    )
    op.create_index('idx_team_era_node_id', 'team_era', ['node_id'])
    op.create_index('idx_team_era_season_year', 'team_era', ['season_year'])
    op.create_index('idx_team_era_tier_level', 'team_era', ['tier_level'])
    
    # Create team_sponsor_link table
    op.create_table('team_sponsor_link',
        sa.Column('link_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('era_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rank_order', sa.Integer(), nullable=False),
        sa.Column('prominence_percent', sa.Integer(), nullable=False),
        sa.Column('hex_color_override', sa.String(length=7), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('rank_order >= 1', name='check_rank_order_positive'),
        sa.CheckConstraint('prominence_percent > 0 AND prominence_percent <= 100', name='check_prominence_range'),
        sa.ForeignKeyConstraint(['brand_id'], ['sponsor_brand.brand_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['era_id'], ['team_era.era_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['last_modified_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('link_id'),
        sa.UniqueConstraint('era_id', 'brand_id', name='uq_era_brand'),
        sa.UniqueConstraint('era_id', 'rank_order', name='uq_era_rank')
    )
    op.create_index('idx_team_sponsor_link_era_id', 'team_sponsor_link', ['era_id'])
    op.create_index('idx_team_sponsor_link_brand_id', 'team_sponsor_link', ['brand_id'])
    
    # Create lineage_event table
    op.create_table('lineage_event',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('predecessor_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('successor_node_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_year', sa.Integer(), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=True),
        sa.Column('event_type', postgresql.ENUM('LEGAL_TRANSFER', 'SPIRITUAL_SUCCESSION', 'MERGE', 'SPLIT', name='lineage_event_type_enum', create_type=False), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('predecessor_node_id != successor_node_id', name='check_not_circular'),
        sa.CheckConstraint('event_year >= 1900 AND event_year <= 2100', name='check_event_year'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['last_modified_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['predecessor_node_id'], ['team_node.node_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['successor_node_id'], ['team_node.node_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('event_id')
    )
    op.create_index('idx_lineage_event_predecessor', 'lineage_event', ['predecessor_node_id'])
    op.create_index('idx_lineage_event_successor', 'lineage_event', ['successor_node_id'])
    op.create_index('idx_lineage_event_year', 'lineage_event', ['event_year'])
    op.create_index('idx_lineage_event_type', 'lineage_event', ['event_type'])
    
    # Create edit_history table
    op.create_table('edit_history',
        sa.Column('edit_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', postgresql.ENUM('CREATE', 'UPDATE', 'DELETE', name='edit_action_enum', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', 'APPLIED', name='edit_status_enum', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('snapshot_before', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('snapshot_after', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('edit_id')
    )
    op.create_index('idx_edit_history_entity', 'edit_history', ['entity_type', 'entity_id'])
    op.create_index('idx_edit_history_user_id', 'edit_history', ['user_id'])
    op.create_index('idx_edit_history_status', 'edit_history', ['status'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_edit_history_status', table_name='edit_history')
    op.drop_index('idx_edit_history_user_id', table_name='edit_history')
    op.drop_index('idx_edit_history_entity', table_name='edit_history')
    op.drop_table('edit_history')
    
    op.drop_index('idx_lineage_event_type', table_name='lineage_event')
    op.drop_index('idx_lineage_event_year', table_name='lineage_event')
    op.drop_index('idx_lineage_event_successor', table_name='lineage_event')
    op.drop_index('idx_lineage_event_predecessor', table_name='lineage_event')
    op.drop_table('lineage_event')
    
    op.drop_index('idx_team_sponsor_link_brand_id', table_name='team_sponsor_link')
    op.drop_index('idx_team_sponsor_link_era_id', table_name='team_sponsor_link')
    op.drop_table('team_sponsor_link')
    
    op.drop_index('idx_team_era_tier_level', table_name='team_era')
    op.drop_index('idx_team_era_season_year', table_name='team_era')
    op.drop_index('idx_team_era_node_id', table_name='team_era')
    op.drop_table('team_era')
    
    op.drop_index('idx_team_node_is_active', table_name='team_node')
    op.drop_index('idx_team_node_dissolution_year', table_name='team_node')
    op.drop_index('idx_team_node_founding_year', table_name='team_node')
    op.drop_index('idx_team_node_legal_name', table_name='team_node')
    op.drop_table('team_node')
    
    op.drop_index('idx_sponsor_brand_master_id', table_name='sponsor_brand')
    op.drop_table('sponsor_brand')
    
    op.drop_index('idx_sponsor_master_protected', table_name='sponsor_master')
    op.drop_index('idx_sponsor_master_legal_name', table_name='sponsor_master')
    op.drop_table('sponsor_master')
    
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_google_id', table_name='users')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute('DROP TYPE lineage_event_type_enum')
    op.execute('DROP TYPE edit_status_enum')
    op.execute('DROP TYPE edit_action_enum')
    op.execute('DROP TYPE user_role_enum')
