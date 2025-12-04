"""
Alembic migration for lineage_event table and event_type_enum
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

# revision identifiers, used by Alembic.
revision = '003_add_lineage_event'
down_revision = '002_add_team_era'
branch_labels = None
depends_on = None

def upgrade():
    dialect = op.get_context().dialect
    
    if dialect.name == 'postgresql':
        # Ensure pgcrypto is available for gen_random_uuid()
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        # Ensure ENUM type exists (guarded for Postgres CI re-runs)
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_type_enum') THEN
                    CREATE TYPE event_type_enum AS ENUM ('LEGAL_TRANSFER', 'SPIRITUAL_SUCCESSION', 'MERGE', 'SPLIT');
                END IF;
            END$$;
            """
        )
        id_type = pg.UUID(as_uuid=True)
        server_default_arg = sa.text('gen_random_uuid()')
        event_type_col = sa.Column('event_type', pg.ENUM(name='event_type_enum', create_type=False), nullable=False)
        created_at_default = sa.text('NOW()')
        updated_at_default = sa.text('NOW()')
    else:
        # SQLite: use CHAR(36) for UUID, STRING for enum
        id_type = sa.CHAR(36)
        server_default_arg = None
        event_type_col = sa.Column('event_type', sa.String(50), nullable=False)
        created_at_default = None
        updated_at_default = None

    # Create lineage_event table
    op.create_table(
        'lineage_event',
        sa.Column('event_id', id_type, primary_key=True, server_default=server_default_arg),
        sa.Column('previous_node_id', id_type, sa.ForeignKey('team_node.node_id', ondelete='SET NULL'), nullable=True),
        sa.Column('next_node_id', id_type, sa.ForeignKey('team_node.node_id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_year', sa.Integer(), nullable=False),
        event_type_col,
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=created_at_default),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=updated_at_default),
        sa.CheckConstraint('(previous_node_id IS NOT NULL OR next_node_id IS NOT NULL)', name='ck_lineage_event_node_not_null'),
        sa.CheckConstraint('event_year >= 1900', name='ck_lineage_event_year_min'),
    )
    op.create_index('idx_lineage_event_prev', 'lineage_event', ['previous_node_id'])
    op.create_index('idx_lineage_event_next', 'lineage_event', ['next_node_id'])
    op.create_index('idx_lineage_event_year', 'lineage_event', ['event_year'])
    op.create_index('idx_lineage_event_type', 'lineage_event', ['event_type'])

def downgrade():
    op.drop_index('idx_lineage_event_type', table_name='lineage_event')
    op.drop_index('idx_lineage_event_year', table_name='lineage_event')
    op.drop_index('idx_lineage_event_next', table_name='lineage_event')
    op.drop_index('idx_lineage_event_prev', table_name='lineage_event')
    op.drop_table('lineage_event')
    # Drop enum type only if it exists and we're on PostgreSQL
    dialect = op.get_context().dialect
    if dialect.name == 'postgresql':
        pg.ENUM(name='event_type_enum').drop(op.get_bind(), checkfirst=True)
