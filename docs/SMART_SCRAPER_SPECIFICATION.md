# Smart Scraper Specification

**Version:** 1.1  
**Date:** 2026-01-04  
**Status:** Approved for Implementation

## 1. Overview

The **Smart Scraper** is a specialized bulk-ingestion tool designed to populate the Chainlines database with historical professional cycling team data. It utilizes a **Large Language Model (LLM)** for complex decisions regarding team lineage (mergers, splits, spiritual successors), sponsor resolution, and data conflict arbitration.

### 1.1 Key Constraints
* **Usage Pattern:** One-time bulk ingestion (populating history) + Annual updates.
* **Execution:** Local execution (developer machine), syncing to production DB.
* **Legal Compliance:** **STRICT EXCLUSION** of ProCyclingStats (PCS) as a data source.

### 1.2 Confidence Threshold
* **Universal Threshold:** **90%**
* **High Confidence (≥90%):** Auto-approve and write directly to DB.
* **Low Confidence (<90%):** Create **PENDING** edit in Audit Log for manual review.

---

## 2. Architecture & Workflow

### 2.1 Phased "Batch Ingestion" Workflow

We execute in **3 Strict Phases** to resolve dependency issues:

#### Phase 1: Discovery & Sponsor Master Resolution
1. **Spidering**: Start at Current Year (2025), walk backwards recursively through "Previous Team" links.
2. **Extraction**: Collect all unique "Sponsor Name Strings" (e.g., "Visma", "Jumbo", "Rabobank").
3. **Resolution (LLM + Search)**:
   * Identify **Master Entity** vs. **Brand Name** (e.g., "AG2R Prévoyance" → Master: "AG2R Group").
   * Determine **Brand Colors** via web search (tie-breaker: iconic color or longest-used color).
   * **Output:** Populate `SponsorMaster` and `SponsorBrand` tables.

#### Phase 2: Team Node Assembly
1. Process the "To-Do List" of teams found in Phase 1.
2. **Validation**: Map scraped sponsor strings to existing `SponsorBrand` UUIDs.
3. **Creation**: Create `TeamNode` and `TeamEra` records.
4. **Sponsor Prominence Rules** (by name appearance order):
   * **1 Sponsor**: 100%
   * **2 Sponsors**: 60% / 40%
   * **3 Sponsors**: 40% / 30% / 30%
   * **4 Sponsors**: 40% / 20% / 20% / 20%
   * **5+ Sponsors**: LLM extends pattern (total must = 100%)
   * **Technical Partners**: Non-title sponsors (bike suppliers, etc.) = **0%**

#### Phase 3: Lineage Connection
1. Scan for "orphan" nodes (e.g., Team A ends 2012, Team B starts 2013 with similar staff).
2. **LLM Reasoning**: Determine relationship type.
3. **Action**: Create `LineageEvent` records to connect the graph.

### 2.2 Ingestion Priority Order
1. **Current WorldTour** teams → scrape full history (even if lower tier in past)
2. **Current ProTeam** teams → full history
3. **Current Continental** teams → full history
4. **Historical-only (pre-1995)** teams → last priority

### 2.3 Termination & Checkpointing
* **Year Floor:** Scrape back to earliest available data across all sources.
* **Checkpointing:** Persist scraper state (URLs visited, current position) so failures can **resume from last checkpoint**.
* **Graceful Backoff:** Exponential backoff on 429/5xx errors before flagging manual intervention.

---

## 3. Data Sources

### 3.1 Primary Source: CyclingFlash
* Establishes the core `TeamNode` continuity and `TeamEra` progression.
* Defines the "skeleton" of the graph.

### 3.2 Secondary Source: CyclingRanking
* Fills gaps and provides deeper historical context.
* Cross-referenced against primary source.

### 3.3 Tertiary Sources (Enrichment)

#### A. Wikipedia / Wikidata (Multi-Language)
* **Languages:** EN, DE, FR, IT, ES, NL (the key cycling nations)
* **Access:** Public APIs (Action API, SPARQL). No API key required.
* **Compliance:** Polite `User-Agent` header (e.g., `ChainlinesBot/1.0 (contact@example.com)`).
* **Usage:** Cross-reference UCI codes, founding dates, official websites, "History" sections for spiritual successor hints.
* **Priority:** Query all 6 language versions; LLM synthesizes across sources.

#### B. Memoire du Cyclisme (via Archive.org)
* **Target:** `memoire-du-cyclisme.eu` (historical deep-dives).
* **Access:** Wayback Machine API (`http://archive.org/wayback/available`).
* **Logic:** Query for **most recent/newest** snapshot (site is a modern archive of history).
* **Constraint:** Low rate-limit to avoid blocks.

### 3.4 Source Conflict Resolution
* **Method:** LLM arbitration when sources disagree.
* If LLM confidence < 90%, flag for manual review regardless.

---

## 4. Technical Implementation

### 4.1 Tech Stack
* **Framework:** FastAPI (Backend Task / Script)
* **LLM Interface:** `instructor` library wrapping Pydantic around Gemini/Deepseek APIs
* **Database:** PostgreSQL (SQLAlchemy Async)

### 4.2 Entry Points
* **CLI:** `python -m app.scraper.run --phase 1 --tier wt` (local dev/testing)
* **API:** `POST /api/admin/scraper/start` (admin-only, background task for remote triggering)

### 4.3 Rate Limits (Configurable Defaults)

| Source | Delay Range | Notes |
|--------|-------------|-------|
| CyclingFlash | 3-6s | Conservative to avoid blocks |
| CyclingRanking | 3-6s | Conservative |
| Archive.org | 5-10s | ~15 req/min documented limit |
| Wikipedia/Wikidata (x6) | 1-3s per domain | Generally permissive; query EN/DE/FR/IT/ES/NL |
| Gemini API | Per quota | Fallback to Deepseek on exhaustion |
| Deepseek API | Per quota | Secondary LLM |

### 4.4 Concurrent Source Workers (Enrichment Optimization)

To maximize throughput while respecting rate limits:

* **Phase 1 (Discovery):** Sequential through CyclingFlash only (builds the team queue).
* **Phase 2+ (Enrichment):** Interleave workers across sources:
  * Worker 1: Fetches CyclingFlash for Team A, B, C...
  * Worker 2: Fetches CyclingRanking for Team A, B, C...
  * Worker 3-8: Fetch Wikipedia (EN/DE/FR/IT/ES/NL) for Team A, B, C...

This way, while Worker 1 waits for its rate-limit delay, other workers can be actively fetching from different sources. Each worker respects its own source's rate limit independently.

### 4.5 LLM Fallback Chain
* **Primary:** Gemini
* **Fallback:** Deepseek (on quota exhaustion or errors)

### 4.5 System Bot User
* **Name:** "Smart Scraper"
* **Creation:** Migration/seed script with fixed UUID
* **Usage:** All `created_by` / `last_modified_by` fields on scraped records

### 4.6 Integration Points
* **Actor:** Scraper runs as the "Smart Scraper" system user.
* **Write Path:** Uses `AuditLogService.create_edit()` for all mutations.
* **Validation:** Uses `LineageEventType` enum for classification.

---

## 5. Key Components

### 5.1 `LLMService` (Intelligence Layer)

**Key Prompts:**

1. `extract_team_data(html: str) -> ScrapedTeamData`
   * Extracts normalized names, sponsors, UCI codes.

2. `decide_lineage(previous_eras: List[TeamEra], current_data: ScrapedTeamData) -> LineageDecision`
   * **Standard Continuation:** `Team A (2023)` → `Team A (2024)` = `LEGAL_TRANSFER`
   * **Absorption (Merge):** `Team Small` joins into `Team Big` (Team Big continues) = `MERGE`
   * **Fusion (Merge):** `Team A` + `Team B` → `Team New` (neither continues) = `MERGE`
   * **Spin-off (Split):** Part of `Team A` forms `Team B` (Team A continues) = `SPLIT`
   * **Dissolution (Split):** `Team A` dies → `Team B` + `Team C` (neither is Team A) = `SPLIT`
   * **Spiritual Succession:** No legal link, but cultural/personnel continuity (e.g., T-Mobile → HTC-Columbia). Best found in Wikipedia "History" sections = `SPIRITUAL_SUCCESSION`

3. `resolve_sponsor_brand(names: List[str]) -> List[SponsorResolution]`
   * Maps raw strings to Master/Brand hierarchy.
   * Determines brand hex color via web search.

### 5.2 `CyclingFlashScraper` (Source Layer)
* Implements `BaseScraper`.
* Iterates backwards from 2025 following "Previous Season" links.
* Handles 429 rate limiting gracefully.

### 5.3 `SmartScraperService` (Orchestration)
* Manages the loop: `Source → LLM → AuditLog`.
* Holds the 90% confidence threshold logic.
* Implements checkpointing for resume capability.

---

## 6. Data Models

### 6.1 `ScrapedTeamData` (Transient)
Pydantic model for raw scrape results.

### 6.2 `LineageDecision` (LLM Output)
```python
class LineageDecision(BaseModel):
    event_type: LineageEventType  # MERGE, SPLIT, LEGAL_TRANSFER, SPIRITUAL_SUCCESSION
    confidence_score: float
    reasoning: str
    predecessor_node_ids: List[UUID]  # Multiple for merges
    successor_node_ids: List[UUID]    # Multiple for splits
    notes: Optional[str]
```

### 6.3 Naming Strategy (LLM Discretion)
* **`legal_name`**: Corporate entity if discoverable; fallback to sponsor-based name.
* **`display_name`**: Common/colloquial name (e.g., "Wolfpack").
* **Tie-breaker:** Latest known name (most recent before dissolution OR current).

---

## 7. Data Integrity & Missing Values

### 7.1 TeamNode
* **`founding_year` (Mandatory):** Initialize with `season_year`. Iteratively update to `min(season_year)` as we scrape backwards.
* **`legal_name` (Mandatory):** Default to registered/sponsor name. Update if enrichment finds corporate entity.

### 7.2 TeamEra
* **`valid_from` (Mandatory):** Default to `{season_year}-01-01` if exact date unknown.
* **`uci_code` / `tier_level` (Optional):** Leave NULL if missing. Do NOT hallucinate.
* **`country_code` (Optional):** 3-letter IOC/UCI code (e.g., NED, GER, ITA). LLM should infer from "Nationality" or "registered in" text fields if possible.
* **Multiple Eras Per Season:** Allowed (different `valid_from` dates) for mid-season rebrands.

---

## 8. Error Handling & Edge Cases
* **Ambiguity:** If source links to multiple previous teams, pass all to LLM for `MERGE` evaluation.
* **Hallucinations:** 90% confidence threshold flags uncertain decisions for review.
* **Anti-Bot:** Random delays (configurable per source) + User-Agent rotation.

---

## 9. Testing Plan

### 9.1 Unit Tests
* `test_llm_decision_logic`: Mock LLM responses, verify `LineageDecision` maps to DB events.
* `test_cycling_flash_parser`: Feed saved HTML files, verify extraction.

### 9.2 Integration Tests
* `test_full_scrape_flow`: Mock HTTP, run service, verify `EditHistory` entry created.

---

## 10. Deployment

### 10.1 Local Development Workflow
1. Run scraper locally against local PostgreSQL.
2. Validate data via admin panel.
3. Export: `pg_dump -Fc chainlines_local > backup.dump`

### 10.2 Production Deployment
* **Option A:** `pg_restore` dump file on VPS PostgreSQL.
* **Option B:** Configure scraper to connect directly to remote DB (use SSH tunnel for security).

### 10.3 Annual Updates
* Trigger via API endpoint (`POST /api/admin/scraper/start --phase 1`) from admin panel.
* Scraper resumes from latest checkpoint or starts fresh for new season.

---

## 11. Database Migrations Required
1. **Relax `check_prominence_range`:** Allow `prominence_percent >= 0` (for 0% technical partners).
2. **Consider `valid_to` on TeamEra:** May be needed if multiple eras per season breaks visualization.

---

## 12. Next Steps
1. Add dependencies to `requirements.txt`: `instructor`, `google-generativeai`, `openai`
2. Create Alembic migration for prominence constraint.
3. Create "Smart Scraper" system user via seed script.
4. Implement `LLMService`.
5. Implement `CyclingFlashScraper` + `CyclingRankingScraper`.
6. Wire together in `SmartScraperService`.
7. Add CLI and API entry points.
