-- ============================================================================
-- ChainLines - PostgreSQL Database Schema DDL
-- Version: 1.0
-- Database: PostgreSQL 15+
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE user_role_enum AS ENUM (
    'EDITOR',
    'TRUSTED_EDITOR',
    'MODERATOR',
    'ADMIN'
);

CREATE TYPE edit_action_enum AS ENUM (
    'CREATE',
    'UPDATE',
    'DELETE'
);

CREATE TYPE edit_status_enum AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED',
    'APPLIED'
);

CREATE TYPE lineage_event_type_enum AS ENUM (
    'LEGAL_TRANSFER',
    'SPIRITUAL_SUCCESSION',
    'MERGE',
    'SPLIT'
);

-- ============================================================================
-- TABLE: users
-- ============================================================================

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    avatar_url VARCHAR(500),
    role user_role_enum NOT NULL DEFAULT 'EDITOR',
    approved_edits_count INTEGER NOT NULL DEFAULT 0,
    is_banned BOOLEAN NOT NULL DEFAULT FALSE,
    banned_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

COMMENT ON TABLE users IS 'User authentication and authorization via Google OAuth';
COMMENT ON COLUMN users.role IS 'EDITOR=submit for approval, TRUSTED_EDITOR=auto-approved, MODERATOR=can review, ADMIN=full control';
COMMENT ON COLUMN users.approved_edits_count IS 'Count of approved edits for auto-promotion to TRUSTED_EDITOR';

-- ============================================================================
-- TABLE: sponsor_master
-- ============================================================================

CREATE TABLE sponsor_master (
    master_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    industry_sector VARCHAR(100),
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    source_url VARCHAR(500),
    source_notes TEXT,
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    last_modified_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sponsor_master_legal_name ON sponsor_master(legal_name);
CREATE INDEX idx_sponsor_master_protected ON sponsor_master(is_protected);

COMMENT ON TABLE sponsor_master IS 'Parent company owning multiple sponsor brands';
COMMENT ON COLUMN sponsor_master.legal_name IS 'Unique internal identifier for parent company';
COMMENT ON COLUMN sponsor_master.display_name IS 'Public-facing name for disambiguation when legal_name conflicts';
COMMENT ON COLUMN sponsor_master.is_protected IS 'When TRUE, requires approval for all edits to master and all brands';

-- ============================================================================
-- TABLE: sponsor_brand
-- ============================================================================

CREATE TABLE sponsor_brand (
    brand_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    master_id UUID NOT NULL REFERENCES sponsor_master(master_id) ON DELETE CASCADE,
    brand_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    default_hex_color VARCHAR(7) NOT NULL CHECK (default_hex_color ~ '^#[0-9A-Fa-f]{6}$'),
    source_url VARCHAR(500),
    source_notes TEXT,
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    last_modified_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_master_brand UNIQUE (master_id, brand_name)
);

CREATE INDEX idx_sponsor_brand_master_id ON sponsor_brand(master_id);
CREATE INDEX idx_sponsor_brand_name ON sponsor_brand(brand_name);

COMMENT ON TABLE sponsor_brand IS 'Individual brand identity under parent company';
COMMENT ON COLUMN sponsor_brand.brand_name IS 'Internal identifier (e.g., Coca-Cola, Sprite) - unique per master';
COMMENT ON COLUMN sponsor_brand.default_hex_color IS 'Brand primary color in #RRGGBB format';

-- ============================================================================
-- TABLE: team_node
-- ============================================================================

CREATE TABLE team_node (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    founding_year INTEGER NOT NULL,
    dissolution_year INTEGER,
    owned_by_sponsor_master_id UUID REFERENCES sponsor_master(master_id) ON DELETE SET NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    latest_team_name VARCHAR(255),
    latest_uci_code VARCHAR(3),
    current_tier INTEGER CHECK (current_tier IN (1, 2, 3)),
    is_active BOOLEAN GENERATED ALWAYS AS (dissolution_year IS NULL) STORED,
    source_url VARCHAR(500),
    source_notes TEXT,
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    last_modified_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_team_node_legal_name ON team_node(legal_name);
CREATE INDEX idx_team_node_founding_year ON team_node(founding_year);
CREATE INDEX idx_team_node_dissolution_year ON team_node(dissolution_year);
CREATE INDEX idx_team_node_protected ON team_node(is_protected);
CREATE INDEX idx_team_node_active ON team_node(is_active);

COMMENT ON TABLE team_node IS 'Persistent team entity (Paying Agent / managerial node)';
COMMENT ON COLUMN team_node.legal_name IS 'Unique internal identifier for team (PAYING AGENT name)';
COMMENT ON COLUMN team_node.founding_year IS 'Year team was founded (soft warn if < 1850 or > current_year + 5)';
COMMENT ON COLUMN team_node.owned_by_sponsor_master_id IS 'Pre-2005: sponsor company owns team';
COMMENT ON COLUMN team_node.is_protected IS 'When TRUE, requires approval for all edits to node, eras, and lineage events';
COMMENT ON COLUMN team_node.latest_team_name IS 'Cached from most recent era for quick access';

-- ============================================================================
-- TABLE: team_era
-- ============================================================================

CREATE TABLE team_era (
    era_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id UUID NOT NULL REFERENCES team_node(node_id) ON DELETE CASCADE,
    season_year INTEGER NOT NULL,
    valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_until DATE,
    registered_name VARCHAR(255) NOT NULL,
    uci_code VARCHAR(3) CHECK (uci_code IS NULL OR (LENGTH(uci_code) = 3 AND uci_code ~ '^[A-Z]{3}$')),
    is_name_auto_generated BOOLEAN NOT NULL DEFAULT TRUE,
    is_manual_override BOOLEAN NOT NULL DEFAULT FALSE,
    is_auto_filled BOOLEAN NOT NULL DEFAULT FALSE,
    tier_level INTEGER CHECK (tier_level IN (1, 2, 3)),
    has_license BOOLEAN NOT NULL DEFAULT FALSE,
    source_origin VARCHAR(50),
    source_url VARCHAR(500),
    source_notes TEXT,
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    last_modified_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_node_year_period UNIQUE (node_id, season_year, valid_from)
);

CREATE INDEX idx_team_era_node_id ON team_era(node_id);
CREATE INDEX idx_team_era_season_year ON team_era(season_year);
CREATE INDEX idx_team_era_tier_level ON team_era(tier_level);
CREATE INDEX idx_team_era_manual_override ON team_era(is_manual_override);

COMMENT ON TABLE team_era IS 'Season-specific team configuration snapshot';
COMMENT ON COLUMN team_era.valid_from IS 'Start date for validity period (handles mid-season changes)';
COMMENT ON COLUMN team_era.registered_name IS 'Official team name (auto-generated from sponsors or manual)';
COMMENT ON COLUMN team_era.uci_code IS '3-letter UCI team code (e.g., TJV for Team Jumbo-Visma)';
COMMENT ON COLUMN team_era.is_name_auto_generated IS 'TRUE if name derived from sponsors';
COMMENT ON COLUMN team_era.is_manual_override IS 'TRUE if manually entered - prevents auto-overwrite during gap-filling';
COMMENT ON COLUMN team_era.is_auto_filled IS 'TRUE if era was automatically created to fill gap between manual entries';
COMMENT ON COLUMN team_era.tier_level IS '1=WorldTeam, 2=ProTeam, 3=Continental (NULL for pre-license era)';
COMMENT ON COLUMN team_era.source_origin IS 'manual, scraped, gap-filled, or cascaded';

-- ============================================================================
-- TABLE: team_sponsor_link
-- ============================================================================

CREATE TABLE team_sponsor_link (
    link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    era_id UUID NOT NULL REFERENCES team_era(era_id) ON DELETE CASCADE,
    brand_id UUID NOT NULL REFERENCES sponsor_brand(brand_id) ON DELETE CASCADE,
    rank_order INTEGER NOT NULL CHECK (rank_order >= 1),
    prominence_percent INTEGER NOT NULL CHECK (prominence_percent > 0 AND prominence_percent <= 100),
    hex_color_override VARCHAR(7) CHECK (hex_color_override IS NULL OR hex_color_override ~ '^#[0-9A-Fa-f]{6}$'),
    source_url VARCHAR(500),
    source_notes TEXT,
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    last_modified_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_era_rank UNIQUE (era_id, rank_order),
    CONSTRAINT uq_era_brand UNIQUE (era_id, brand_id)
);

CREATE INDEX idx_team_sponsor_link_era_id ON team_sponsor_link(era_id);
CREATE INDEX idx_team_sponsor_link_brand_id ON team_sponsor_link(brand_id);

COMMENT ON TABLE team_sponsor_link IS 'Sponsorship contract linking brand to team era';
COMMENT ON COLUMN team_sponsor_link.rank_order IS 'Sponsor ranking (1 = main sponsor, 2 = co-sponsor, etc.)';
COMMENT ON COLUMN team_sponsor_link.prominence_percent IS 'Visual weight in jersey (1-100, should sum to 100% per era)';
COMMENT ON COLUMN team_sponsor_link.hex_color_override IS 'Overrides brand default color for this specific sponsorship';

-- ============================================================================
-- TABLE: lineage_event
-- ============================================================================

CREATE TABLE lineage_event (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    predecessor_node_id UUID NOT NULL REFERENCES team_node(node_id) ON DELETE CASCADE,
    successor_node_id UUID NOT NULL REFERENCES team_node(node_id) ON DELETE CASCADE,
    event_year INTEGER NOT NULL CHECK (event_year >= 1900 AND event_year <= 2100),
    event_date DATE,
    event_type lineage_event_type_enum NOT NULL,
    notes TEXT,
    source_url VARCHAR(500),
    source_notes TEXT,
    created_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    last_modified_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT check_not_circular CHECK (predecessor_node_id != successor_node_id)
);

CREATE INDEX idx_lineage_event_predecessor ON lineage_event(predecessor_node_id);
CREATE INDEX idx_lineage_event_successor ON lineage_event(successor_node_id);
CREATE INDEX idx_lineage_event_year ON lineage_event(event_year);
CREATE INDEX idx_lineage_event_type ON lineage_event(event_type);

COMMENT ON TABLE lineage_event IS 'Structural relationships between team nodes (mergers, splits, transfers, succession)';
COMMENT ON COLUMN lineage_event.event_date IS 'Specific date of event (defaults to Jan 1 of event_year if NULL)';
COMMENT ON COLUMN lineage_event.event_type IS 'LEGAL_TRANSFER, SPIRITUAL_SUCCESSION, MERGE (stored as multiple A→C, B→C), SPLIT (A→B, A→C)';

-- ============================================================================
-- TABLE: edit_history
-- ============================================================================

CREATE TABLE edit_history (
    edit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action edit_action_enum NOT NULL,
    status edit_status_enum NOT NULL DEFAULT 'PENDING',
    reviewed_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    snapshot_before JSONB,
    snapshot_after JSONB NOT NULL,
    source_url VARCHAR(500),
    source_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_edit_history_entity ON edit_history(entity_type, entity_id);
CREATE INDEX idx_edit_history_user_id ON edit_history(user_id);
CREATE INDEX idx_edit_history_status ON edit_history(status);
CREATE INDEX idx_edit_history_reviewed_by ON edit_history(reviewed_by);
CREATE INDEX idx_edit_history_created_at ON edit_history(created_at DESC);

COMMENT ON TABLE edit_history IS 'Wikipedia-style revision history with full snapshots';
COMMENT ON COLUMN edit_history.entity_type IS 'Table name (team_node, team_era, sponsor_master, sponsor_brand, team_sponsor_link, lineage_event)';
COMMENT ON COLUMN edit_history.status IS 'PENDING=awaiting review, APPROVED=approved by moderator, REJECTED=rejected, APPLIED=auto-applied (trusted user)';
COMMENT ON COLUMN edit_history.snapshot_before IS 'Full record state before edit (NULL for CREATE)';
COMMENT ON COLUMN edit_history.snapshot_after IS 'Full record state after edit';

-- ============================================================================
-- TRIGGERS FOR updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sponsor_master_updated_at
    BEFORE UPDATE ON sponsor_master
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_sponsor_brand_updated_at
    BEFORE UPDATE ON sponsor_brand
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_team_node_updated_at
    BEFORE UPDATE ON team_node
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_team_era_updated_at
    BEFORE UPDATE ON team_era
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_team_sponsor_link_updated_at
    BEFORE UPDATE ON team_sponsor_link
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_lineage_event_updated_at
    BEFORE UPDATE ON lineage_event
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA (SYSTEM USER)
-- ============================================================================

INSERT INTO users (
    user_id,
    google_id,
    email,
    display_name,
    role,
    created_at
) VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system',
    'system@chainlines.internal',
    'System',
    'ADMIN',
    NOW()
) ON CONFLICT (google_id) DO NOTHING;

COMMENT ON TABLE users IS 'Initial system user created for backfilling created_by fields and automated processes';

-- ============================================================================
-- VIEWS (Optional - for convenience)
-- ============================================================================

-- View: Active teams with latest era information
CREATE VIEW v_active_teams AS
SELECT 
    tn.node_id,
    tn.legal_name,
    tn.display_name,
    tn.founding_year,
    tn.latest_team_name,
    tn.latest_uci_code,
    tn.current_tier,
    tn.is_protected
FROM team_node tn
WHERE tn.is_active = TRUE;

-- View: Complete team timeline with eras
CREATE VIEW v_team_timeline AS
SELECT 
    tn.node_id,
    tn.legal_name AS node_legal_name,
    tn.founding_year,
    tn.dissolution_year,
    te.era_id,
    te.season_year,
    te.registered_name,
    te.uci_code,
    te.tier_level,
    te.is_manual_override,
    te.is_auto_filled
FROM team_node tn
JOIN team_era te ON te.node_id = tn.node_id
ORDER BY tn.founding_year, te.season_year;

-- View: Sponsor composition per era
CREATE VIEW v_era_sponsors AS
SELECT 
    te.era_id,
    te.node_id,
    te.season_year,
    te.registered_name,
    tsl.rank_order,
    sb.brand_name,
    sm.legal_name AS parent_company,
    tsl.prominence_percent,
    COALESCE(tsl.hex_color_override, sb.default_hex_color) AS display_color
FROM team_era te
JOIN team_sponsor_link tsl ON tsl.era_id = te.era_id
JOIN sponsor_brand sb ON sb.brand_id = tsl.brand_id
JOIN sponsor_master sm ON sm.master_id = sb.master_id
ORDER BY te.season_year, te.node_id, tsl.rank_order;

-- View: Pending edits for moderation queue
CREATE VIEW v_pending_edits AS
SELECT 
    eh.edit_id,
    eh.entity_type,
    eh.entity_id,
    eh.action,
    u.display_name AS submitted_by,
    u.email AS submitter_email,
    eh.created_at AS submitted_at,
    eh.snapshot_after
FROM edit_history eh
JOIN users u ON u.user_id = eh.user_id
WHERE eh.status = 'PENDING'
ORDER BY eh.created_at ASC;

-- ============================================================================
-- GRANTS (Adjust based on your authentication setup)
-- ============================================================================

-- Example: Grant read access to application role
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_read_role;
-- GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_write_role;

-- ============================================================================
-- SCHEMA VALIDATION
-- ============================================================================

-- Query to validate foreign key relationships
SELECT 
    tc.table_name AS child_table,
    kcu.column_name AS child_column,
    ccu.table_name AS parent_table,
    ccu.column_name AS parent_column,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;

-- ============================================================================
-- END OF DDL
-- ============================================================================