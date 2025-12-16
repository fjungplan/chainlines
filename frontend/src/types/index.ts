/**
 * Frontend TypeScript Definitions
 * These interfaces match the Backend API response shapes.
 */

// --- Enums ---

export enum LineageEventType {
    LEGAL_TRANSFER = 'LEGAL_TRANSFER',
    SPIRITUAL_SUCCESSION = 'SPIRITUAL_SUCCESSION',
    MERGE = 'MERGE',
    SPLIT = 'SPLIT',
}

// --- Timeline API Models (for TimelineGraph) ---

export interface SponsorComposition {
    brand: string;
    color: string; // Hex color
    prominence: number; // 0-100
}

export interface TimelineEra {
    era_id: string;
    year: number; // Mapped from season_year
    name: string; // Mapped from registered_name
    tier?: number; // Mapped from tier_level
    uci_code?: string;
    sponsors: SponsorComposition[];
}

export interface TimelineNode {
    id: string; // Node ID
    founding_year: number;
    dissolution_year?: number;
    eras: TimelineEra[];
}

export interface TimelineLink {
    source: string; // Node ID
    target: string; // Node ID
    year: number;
    type: string; // LineageEventType
}

export interface TimelineMeta {
    year_range: [number, number];
    node_count: number;
    link_count: number;
}

export interface TimelineResponse {
    nodes: TimelineNode[];
    links: TimelineLink[];
    meta: TimelineMeta;
}

// --- Team Detail API Models (for TeamDetailPage) ---

export interface TransitionInfo {
    year: number;
    name?: string;
    event_type: string;
}

export interface TeamHistoryEra {
    year: number;
    name: string;
    tier?: number;
    uci_code?: string;
    status: string;
    predecessor?: TransitionInfo;
    successor?: TransitionInfo;
}

export interface LineageSummary {
    has_predecessors: boolean;
    has_successors: boolean;
    spiritual_succession: boolean;
}

export interface TeamHistoryResponse {
    node_id: string;
    founding_year: number;
    dissolution_year?: number;
    timeline: TeamHistoryEra[];
    lineage_summary: LineageSummary;
}

// --- Team List API Models ---

export interface TeamNodeResponse {
    node_id: string;
    legal_name: string;
    display_name?: string;
    founding_year: number;
    dissolution_year?: number;
    is_active: boolean;
    latest_team_name?: string;
    latest_uci_code?: string;
    current_tier?: number;
    created_at: string;
}

export interface TeamListResponse {
    items: TeamNodeResponse[];
    total: number;
    skip: number;
    limit: number;
}
