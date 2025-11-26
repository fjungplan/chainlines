# Professional Cycling Team Timeline Visualization - Complete Specification

## 1. Project Overview

### 1.1 Purpose
Create a comprehensive web-based visualization displaying the historical timeline of all professional cycling teams from 1900 to present, tracking team lineages through name changes, sponsorship changes, mergers, splits, and other transformations.

### 1.2 Core Challenge
Professional cycling teams maintain continuity through "spiritual" succession rather than purely legal entities. The same core staff, riders, and management may continue under different legal ownership, sponsors, and team names. The system must track these complex relationships accurately.

### 1.3 Key Features
- Interactive horizontal Sankey-style timeline visualization
- Dynamic sponsor history tracking across multiple teams
- Team lineage tracing through succession events
- Automated data scraping from multiple authoritative sources
- Manual data curation and conflict resolution backend
- Comprehensive audit trail and version history

---

## 2. Conceptual Framework

### 2.1 Core Entity: The "Spiritual Team"
The fundamental entity is the **Team Lineage** (Lineage ID), representing the continuous "spiritual" entity that persists through:
- Sponsor changes
- Name changes
- Legal ownership transfers
- License transfers
- Staff/rider transitions

### 2.2 Team Timeline Slots
Each distinct configuration of a team (specific name, sponsor combination, ownership) exists within a **Team Timeline Slot** with precise start and end dates. These slots are linked together through their Lineage ID.

### 2.3 Succession Relationships
Teams are connected through qualified succession links:

1. **Direct Continuation** - Same management/ownership, only name/sponsor changes
2. **License Sale** - Formal license transfer to new legal entity
3. **Qualified Succession (Majority)** - >50% of staff/riders/management transfer to new entity
4. **Split/Fork** - Team dissolves, personnel divided into 2+ new entities
5. **Partial Split-off** - Portion of staff forms new team while original continues
6. **Merge/Acquisition** - Team joins existing team (asymmetrical)
7. **Equal Merger** - Two teams combine on equal terms
8. **New Lineage** - Explicit break, fresh start with no predecessor

---

## 3. Data Model Architecture

### 3.1 Core Tables

#### Team_Entity (Timeline Slot)
The minimal, fundamental record representing a team during a specific period.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `entity_id` | UUID/String | Primary key | Unique, required |
| `lineage_id` | UUID/String | Foreign key to Lineage table | Required, indexed |
| `start_date` | Date (YYYY-MM-DD) | When this configuration began | Required |
| `end_date` | Date (YYYY-MM-DD) or NULL | When this configuration ended (NULL = currently active) | Required or NULL |
| `created_at` | Timestamp | Record creation timestamp | Auto-generated |
| `updated_at` | Timestamp | Last modification timestamp | Auto-updated |

**Indexes**: `lineage_id`, `start_date`, `end_date`

#### Team_Lineage
Represents the continuous "spiritual" team entity.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `lineage_id` | UUID/String | Primary key | Unique, required |
| `primary_name` | String | Most recognizable/current name for this lineage | Optional, for display |
| `founding_year` | Integer | Approximate founding year | Optional |
| `notes` | Text | Historical context or special notes | Optional |
| `created_at` | Timestamp | Record creation | Auto-generated |

#### Team_Property_Link
Time-bound properties that can change within a Team_Entity's lifetime.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `property_id` | UUID/String | Primary key | Unique, required |
| `entity_id` | UUID/String | Foreign key to Team_Entity | Required, indexed |
| `property_type` | Enum | Type of property | Required: `NAME`, `UCI_CODE`, `TIER`, `NATIONALITY`, `OWNER` |
| `property_value` | String | The actual value | Required |
| `start_date` | Date | When this property value became effective | Required |
| `end_date` | Date or NULL | When this property value ended | Required or NULL |
| `confidence_score` | Float (0-1) | Data confidence level | Optional, 0.0-1.0 |
| `source_references` | JSON Array | Array of source URLs/IDs | Optional |
| `notes` | Text | Additional context | Optional |

**Indexes**: `entity_id`, `property_type`, `start_date`

**Property Types**:
- `NAME` - Full team name for this period
- `UCI_CODE` - Official UCI code (e.g., "SOQ")
- `TIER` - Foreign key to Tier_Level
- `NATIONALITY` - ISO country code
- `OWNER` - Legal owner/management company name

### 3.2 Sponsor Management

#### Sponsor_Master
Master record for each sponsor entity (company/organization).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `sponsor_id` | UUID/String | Primary key | Unique, required |
| `legal_name` | String | Official legal name of sponsor | Required |
| `parent_company` | String | Parent organization, if applicable | Optional |
| `country` | String | Country of origin | Optional |
| `industry_sector` | String | Business sector | Optional |
| `website` | String | Official website | Optional |
| `notes` | Text | Additional information | Optional |
| `created_at` | Timestamp | Record creation | Auto-generated |

#### Sponsor_Brand_History
Tracks different brand names used by sponsors over time.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `brand_id` | UUID/String | Primary key | Unique, required |
| `sponsor_id` | UUID/String | Foreign key to Sponsor_Master | Required, indexed |
| `brand_name` | String | Brand/marketing name used | Required |
| `start_date` | Date | When this brand name began | Required |
| `end_date` | Date or NULL | When this brand name ended | Required or NULL |
| `is_primary` | Boolean | Whether this is the primary brand | Default: FALSE |
| `notes` | Text | Context for brand name change | Optional |

**Example**: Telekom → T-Mobile, AG2R La Mondiale → AG2R Prévoyance

#### Team_Sponsor_Link
Connects sponsors to teams for specific periods with ranking.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `link_id` | UUID/String | Primary key | Unique, required |
| `entity_id` | UUID/String | Foreign key to Team_Entity | Required, indexed |
| `brand_id` | UUID/String | Foreign key to Sponsor_Brand_History | Required, indexed |
| `sponsor_rank` | Enum | Type/level of sponsorship | Required |
| `display_order` | Integer | Position in team name (1, 2, 3...) | Required for title sponsors |
| `start_date` | Date | When sponsorship began | Required |
| `end_date` | Date or NULL | When sponsorship ended | Required or NULL |
| `confidence_score` | Float | Data confidence | Optional, 0.0-1.0 |
| `source_references` | JSON Array | Supporting sources | Optional |

**Sponsor Ranks** (Enum values):
- `TITLE_PRIMARY` - Primary title sponsor (first in name)
- `TITLE_SECONDARY` - Co-title sponsor
- `TITLE_TERTIARY` - Third-level title sponsor
- `MAJOR` - Major sponsor (not in title)
- `BIKE` - Bike/equipment supplier
- `APPAREL` - Kit/clothing supplier
- `HELMET` - Helmet supplier
- `MINOR` - Minor/supporting sponsor
- `TECHNICAL` - Technical partner
- `RESERVE_1` through `RESERVE_5` - Reserved for future categories

### 3.3 Team Succession/Lineage Links

#### Team_Succession_Link
Defines relationships between Team_Entity records across lineages.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `link_id` | UUID/String | Primary key | Unique, required |
| `source_entity_id` | UUID/String | Predecessor team entity | Required, indexed |
| `target_entity_id` | UUID/String | Successor team entity | Required, indexed |
| `link_type` | Enum | Type of succession | Required |
| `link_qualifier` | Enum | Additional qualifier for asymmetry | Optional |
| `transition_date` | Date (YYYY-MM) | When transition occurred | Required |
| `staff_transfer_percentage` | Integer (0-100) | Approximate % of staff transferred | Optional |
| `confidence_score` | Float (0-1) | Confidence in this link | Optional |
| `source_references` | JSON Array | Supporting documentation | Required (multiple) |
| `notes` | Text | Explanatory text | Optional |
| `manual_override` | Boolean | Was this manually created/edited? | Default: FALSE |
| `created_at` | Timestamp | Record creation | Auto-generated |
| `created_by` | String | User who created (if authenticated) | Optional |

**Link Types**:
- `DIRECT_CONTINUATION` - Same management, name change only
- `LICENSE_SALE` - License sold to new entity
- `QUALIFIED_SUCCESSION` - Majority transfer (>50%)
- `SPLIT_EQUAL` - Team divides into equal parts
- `SPLIT_MAJOR_MINOR` - Unequal split
- `PARTIAL_SPLIT` - Some staff leave, original continues
- `MERGE_EQUAL` - Two teams combine equally
- `ACQUISITION` - One team absorbed by another
- `NEW_LINEAGE` - Explicit break, no predecessor

**Link Qualifiers** (optional, for asymmetrical relationships):
- `MAJOR_PORTION` - Majority of original team
- `MINOR_PORTION` - Minority of original team
- `PARTIAL_STAFF` - Partial staff transfer while original continues
- `LICENSE_ONLY` - Only license transferred, minimal staff
- `SPONSOR_DRIVEN` - Change driven primarily by sponsor movement

**Indexes**: `source_entity_id`, `target_entity_id`, `link_type`

### 3.4 UCI Tier Management

#### UCI_Tier_Definition
Defines the consistent tier system across all years.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `tier_id` | String | Primary key (e.g., "T1", "T2", "T3") | Unique, required |
| `tier_level` | Integer | Numeric hierarchy (1 = highest) | Required, unique |
| `description` | String | General description | Required |
| `notes` | Text | Additional context | Optional |

**Example Data**:
- `T1`, Level 1: "Top tier professional teams"
- `T2`, Level 2: "Second tier professional teams"
- `T3`, Level 3: "Continental level teams"
- `T4`, Level 4: "Amateur/regional teams"

#### UCI_Tier_Label_History
Maps UCI's changing terminology to consistent tiers.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `label_id` | UUID/String | Primary key | Unique, required |
| `tier_id` | String | Foreign key to UCI_Tier_Definition | Required, indexed |
| `official_label` | String | UCI's official label for this period | Required |
| `start_year` | Integer | Year this label began | Required |
| `end_year` | Integer or NULL | Year this label ended | Required or NULL |
| `region` | String | If label varies by region | Optional |

**Example Data**:
- T1, "WorldTour", 2011-2018
- T1, "UCI WorldTeam", 2019-present
- T1, "UCI ProTeam", 2005-2010
- T1, "Division 1", 1997-2004
- T2, "UCI ProTeam", 2019-present
- T2, "Professional Continental", 2005-2018

### 3.5 Supporting Tables

#### Data_Source
Registry of all data sources used.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `source_id` | UUID/String | Primary key | Unique, required |
| `source_name` | String | Display name | Required |
| `source_type` | Enum | Type of source | Required: `WIKIPEDIA`, `DATABASE`, `OFFICIAL`, `MANUAL` |
| `base_url` | String | Base URL for the source | Optional |
| `language` | String | Language code (for Wikipedia) | Optional |
| `reliability_score` | Float (0-1) | General reliability rating | Optional |
| `priority_rank` | Integer | Priority for conflict resolution | Required |
| `scraping_enabled` | Boolean | Is automated scraping allowed? | Default: FALSE |
| `last_scraped` | Timestamp | Last successful scrape | Optional |
| `notes` | Text | Additional information | Optional |

**Priority Ranks** (for conflict resolution):
1. ProCyclingStats (gold standard)
2. Wikipedia (multiple languages)
3. FirstCycling
4. CyclingFlash
5. CyclingRanking
6. CQRanking
7. UCI Official (if accessible)
8. Manual entry

#### Data_Conflict
Tracks unresolved or resolved conflicts from scraping.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `conflict_id` | UUID/String | Primary key | Unique, required |
| `entity_id` | UUID/String | Related Team_Entity (if applicable) | Optional, indexed |
| `conflict_type` | Enum | Type of data conflict | Required |
| `field_name` | String | Which field has conflict | Required |
| `conflicting_values` | JSON Object | All conflicting values with sources | Required |
| `resolution_status` | Enum | Current status | Required |
| `resolved_value` | String | Final chosen value | Optional (when resolved) |
| `resolution_method` | Enum | How it was resolved | Optional |
| `resolved_by` | String | User who resolved | Optional |
| `resolved_at` | Timestamp | When resolved | Optional |
| `notes` | Text | Context and reasoning | Optional |
| `created_at` | Timestamp | When conflict was detected | Auto-generated |

**Conflict Types**:
- `DATE_MISMATCH` - Start/end dates differ
- `NAME_VARIATION` - Different team names
- `SPONSOR_CONFLICT` - Different sponsor information
- `LINEAGE_DISAGREEMENT` - Different succession interpretations
- `TIER_MISMATCH` - Different tier classifications
- `NATIONALITY_CONFLICT` - Different country assignments

**Resolution Status**:
- `PENDING` - Awaiting review
- `UNDER_REVIEW` - Currently being examined
- `RESOLVED_AUTO` - Auto-resolved by rules
- `RESOLVED_MANUAL` - Manually resolved
- `DEFERRED` - Marked for later review
- `ACKNOWLEDGED` - Conflict noted but accepted as ambiguous

**Resolution Methods**:
- `GOLD_STANDARD` - Used ProCyclingStats value
- `WIKIPEDIA_MAJORITY` - Majority across Wikipedia sources
- `MANUAL_DECISION` - Administrator chose value
- `CUSTOM_VALUE` - Administrator entered new value
- `SOURCE_PRIORITY` - Used highest priority source

#### Audit_Log
Complete history of all data changes.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `log_id` | UUID/String | Primary key | Unique, required |
| `timestamp` | Timestamp | When change occurred | Auto-generated, indexed |
| `user_id` | String | User who made change | Optional (for authenticated system) |
| `action_type` | Enum | Type of action | Required |
| `table_name` | String | Which table was affected | Required |
| `record_id` | String | ID of affected record | Required |
| `field_name` | String | Which field changed | Optional |
| `old_value` | Text | Previous value | Optional |
| `new_value` | Text | New value | Optional |
| `change_reason` | Text | Explanation for change | Optional |
| `related_conflict_id` | UUID/String | Link to Data_Conflict if applicable | Optional |
| `ip_address` | String | IP address of change origin | Optional |

**Action Types**:
- `INSERT` - New record created
- `UPDATE` - Existing record modified
- `DELETE` - Record deleted
- `CONFLICT_RESOLVED` - Conflict resolution
- `SCRAPE_UPDATE` - Automated scraping update
- `BULK_IMPORT` - Batch data import
- `MANUAL_OVERRIDE` - Manual data correction

**Indexes**: `timestamp`, `table_name`, `record_id`, `user_id`

### 3.6 Additional Metadata Tables

#### Color_Scheme
Stores color information for sponsors/teams for visualization.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `color_id` | UUID/String | Primary key | Unique, required |
| `entity_type` | Enum | What this color applies to | Required: `SPONSOR_BRAND`, `TEAM_PERIOD` |
| `entity_id` | UUID/String | Foreign key to relevant entity | Required, indexed |
| `primary_color` | String (Hex) | Main color (hex code) | Required |
| `secondary_color` | String (Hex) | Secondary color | Optional |
| `tertiary_color` | String (Hex) | Third color | Optional |
| `start_date` | Date | When these colors were valid | Required |
| `end_date` | Date or NULL | When these colors changed | Required or NULL |
| `source` | String | Where color info was obtained | Optional |
| `notes` | Text | Additional context | Optional |

**Example**: Team Sky white/black (2010-2018), Ineos black/red (2019-2020), Ineos red/white (2021-present)

---

## 4. Data Retrieval & Processing

### 4.1 Scraping Sources

#### Primary Sources (Prioritized)
1. **ProCyclingStats** (procyclingstats.com) - GOLD STANDARD
   - Most comprehensive and reliable
   - Team pages with full history
   - Roster information
   - Sponsor details
   
2. **Wikipedia** (multiple languages)
   - German (de.wikipedia.org)
   - French (fr.wikipedia.org)
   - Spanish (es.wikipedia.org)
   - English (en.wikipedia.org)
   - Italian (it.wikipedia.org)
   - Dutch (nl.wikipedia.org)
   - Team infoboxes contain structured data
   - Articles contain narrative succession information
   
3. **FirstCycling** (firstcycling.com)
   - Good historical data
   - Team hierarchies
   
4. **CyclingFlash** (cyclingflash.com)
   - Current data
   
5. **CyclingRanking** (cyclingranking.com)
   - Rankings and team info
   
6. **CQRanking** (cqranking.com)
   - Historical rankings
   
7. **UCI Official** (if accessible)
   - Official team registrations
   - License information

### 4.2 Scraping Strategy

#### 4.2.1 Data Extraction Points
For each source, extract:
- Team names (all variations)
- Start and end dates (as precise as possible)
- Sponsor information
- Nationality
- UCI codes (when available)
- Tier/division
- Successor/predecessor relationships (explicit or implicit)
- Manager/owner information
- Historical notes and context

#### 4.2.2 Scraping Frequency
- **Initial Load**: One-time comprehensive scrape of all sources
- **Regular Updates**: Weekly scrape of current season data
- **Historical Updates**: Monthly scrape for historical corrections
- **Manual Trigger**: Allow admin to trigger immediate scrape of specific team/source

#### 4.2.3 Scraping Process Flow
```
1. Identify target pages (team lists, individual team pages)
2. Extract raw data
3. Parse and structure data
4. Normalize formats (dates, names, codes)
5. Calculate confidence scores
6. Compare with existing data
7. Identify conflicts
8. Flag new/updated information
9. Auto-resolve simple conflicts (same value from multiple sources)
10. Create conflict records for ambiguous cases
11. Update database
12. Log all changes
```

### 4.3 Data Cleaning & Standardization

#### 4.3.1 Date Normalization
- Parse various date formats: "2010", "01/2010", "January 2010", "2010-01-15"
- Standardize to YYYY-MM-DD format
- Handle ambiguous dates:
  - "2010" → "2010-01-01" (with confidence flag)
  - "mid-2010" → "2010-07-01" (with confidence flag)
  - "end of 2010" → "2010-12-31" (with confidence flag)

#### 4.3.2 Name Standardization
- Remove extra whitespace
- Standardize punctuation (hyphens vs spaces)
- Handle special characters (é, ñ, ü, etc.)
- Track name variations as aliases
- Detect sponsor name within team name
- Examples:
  - "T-Mobile Team" = "T-Mobile" = "T - Mobile" = "Team T-Mobile"
  - "Mapei - Quick Step" = "Mapei-QuickStep" = "Mapei Quick-Step"

#### 4.3.3 Country Code Standardization
- Convert all country references to ISO 3166-1 alpha-2 codes
- Handle historical countries (USSR, Yugoslavia, etc.)
- Handle name variations:
  - "Great Britain" = "United Kingdom" = "GB"
  - "Netherlands" = "Holland" = "NL"

#### 4.3.4 Sponsor Detection
- Extract sponsor names from team names
- Match against known sponsor database
- Detect sponsor brand variations
- Identify parent companies

### 4.4 Conflict Resolution System

#### 4.4.1 Automatic Resolution Rules
Conflicts are auto-resolved when:
1. **Unanimous Agreement**: All sources agree (confidence = 1.0)
2. **Gold Standard + Majority**: ProCyclingStats agrees with >50% of other sources
3. **Minor Formatting**: Only whitespace/punctuation differences
4. **Date Precision**: Same month/year but different days (use more precise if available)

#### 4.4.2 Conflict Detection Triggers
Create conflict record when:
- Date differs by >1 day across sources
- Team name differs substantially (not just formatting)
- Sponsor information contradicts
- Lineage relationships disagree
- Tier classification differs
- Nationality differs

#### 4.4.3 Conflict Resolution Workflow
```
1. Detect conflict during data import
2. Create Data_Conflict record with all values
3. Apply automatic resolution rules
4. If auto-resolved:
   - Mark conflict as RESOLVED_AUTO
   - Store chosen value
   - Keep conflict record for audit
5. If manual resolution needed:
   - Mark conflict as PENDING
   - Queue for admin review
6. Admin reviews in Conflict Resolution Dashboard
7. Admin selects or enters resolution
8. System records resolution in conflict record
9. System creates Audit_Log entry
10. Update related Team_Entity/Property records
```

#### 4.4.4 Wikipedia Narrative Parsing
Special handling for Wikipedia articles:
- Parse infobox for structured data
- Parse article text for succession narratives
- Look for keywords:
  - "merged with", "split into", "became", "reformed as"
  - "folded", "dissolved", "ceased operations"
  - "license transferred", "team reformed"
  - "majority of staff joined", "riders moved to"
- Extract context around these keywords
- Present as evidence in conflict resolution

### 4.5 Confidence Scoring

#### 4.5.1 Confidence Score Calculation
For each data point, calculate confidence (0.0-1.0):

```
Base Score:
- ProCyclingStats: 1.0
- Wikipedia (any): 0.85
- FirstCycling: 0.8
- Other DB sources: 0.75
- Manual entry: 1.0 (if verified), 0.9 (if new)

Modifiers:
+ Source count agreement: +0.05 per additional agreeing source (max +0.15)
+ Date precision: +0.05 if day-level precision available
- Conflicting sources: -0.1 per conflicting source
- Ambiguous narrative: -0.15
- Inference/assumption: -0.2

Final Score: Bounded between 0.0 and 1.0
```

#### 4.5.2 Confidence Display
- High confidence (0.85-1.0): No warning indicator
- Medium confidence (0.6-0.84): Yellow/amber indicator
- Low confidence (<0.6): Red indicator, show in metadata panel

---

## 5. Frontend Visualization

### 5.1 Visual Design Concept

#### 5.1.1 Modified Horizontal Sankey Network
- **X-axis**: Timeline (1900-2025)
- **Y-axis**: Team lineages (rows)
- **Visual Elements**:
  - Horizontal bars/lanes representing Team_Entity periods
  - Width represents time duration
  - Color represents primary sponsor
  - Connections between bars show succession relationships
  - Bar height consistent within same lineage

#### 5.1.2 Color System
**Primary Colors** (from Sponsor Brand):
- Each sponsor brand has defined color palette
- Team bar displays primary sponsor color during that period
- Horizontal gradient/fade when sponsor changes
- Vertical gradient within bar shows secondary colors

**Example Transitions**:
- Movistar lineage: Red/blue → White/blue
- Sky/Ineos lineage: White/black → Black/red → Red/white

**Color Accessibility**:
- Support for colorblind modes (protanopia, deuteranopia)
- Alternative: Pattern fills alongside colors
- Ensure sufficient contrast for readability

#### 5.1.3 Visual Hierarchy
**Z-index layers** (back to front):
1. Timeline grid lines (faint)
2. Non-highlighted team bars (reduced opacity)
3. Connection lines between teams (thin, gray)
4. Highlighted team bars (full opacity)
5. Active connection lines (bold, colored)
6. Hover highlights (glow effect)
7. Labels and text
8. UI controls and panels

### 5.2 Layout & Navigation

#### 5.2.1 Default View
- **Time Range**: Last 10 years from current date
- **Teams Displayed**: Top tier (T1) teams only (~18 teams)
- **Zoom Level**: Comfortable reading size (approximately 1 year = 100-150px)
- **Position**: Current date at 75% of viewport width (showing future space)

#### 5.2.2 Viewport Controls

**Zoom Controls**:
- Mouse wheel: Zoom in/out (centered on pointer position)
- Pinch gesture: Zoom (on touch devices)
- Zoom buttons: +/- buttons in corner
- Fit-to-view button: Reset to show entire timeline
- Zoom levels: 
  - Max out: Entire 125 years visible
  - Max in: 1 year fills viewport

**Pan Controls**:
- Click and drag: Pan horizontally and vertically
- Two-finger drag: Pan (on touch devices)
- Arrow keys: Pan in small increments
- Scroll bars: Traditional scrolling

**Time Range Selector**:
- Dual-handle slider below main visualization
- Shows miniature timeline overview
- Displays current viewport position
- Click/drag handles to set range
- Text inputs for precise year entry
  - "From Year": ____
  - "To Year": ____
  - "Apply" button

**Tier Filter**:
- Checkboxes or toggle buttons:
  - ☑ Tier 1 (WorldTour)
  - ☑ Tier 2 (ProTeam)
  - ☐ Tier 3 (Continental)
  - ☐ Tier 4 (Regional/Amateur)
- "Select All" / "Deselect All" buttons
- Filter applies immediately

**Search Box**:
- Global search for teams, sponsors, or people
- Autocomplete suggestions
- Results highlight in visualization
- Jump-to-result button

### 5.3 Interaction Behaviors

#### 5.3.1 Hover Interactions

**Hover over Team Bar**:
- Effect: Subtle glow around bar
- Display: Tooltip with basic info
  - Team name
  - Date range
  - Primary sponsor
  - Tier level
- Highlight: All segments of same lineage with lighter glow
- Delay: 200ms before tooltip appears

**Hover over Sponsor Name** (in bar or tooltip):
- Effect: Strong glow on all bars with this sponsor
- Highlight: All time periods where this sponsor appears
- Visual: Fade/dim all non-matching teams
- Display: Count indicator (e.g., "5 teams sponsored")

**Hover over Connection Line**:
- Effect: Thicken line, show glow
- Display: Tooltip with succession type
  - "License Sale: 2015-01"
  - "Split: 2010-12"
- Highlight: Both connected team bars

#### 5.3.2 Click Interactions

**Click on Team Bar** (primary interaction):
1. **Visual Changes**:
   - Strong highlight on clicked bar (border + glow)
   - Highlight entire lineage (predecessors + successors) with medium glow
   - Fade all non-lineage teams to 30% opacity
   - Bold/highlight all connection lines in lineage
   - Animate connections (subtle pulse)

2. **Sidebar Panel Opens** (right side, 400px width):
   - **Header**: Lineage name + icon
   - **Timeline Summary**: Chronological list:
     ```
     1972-1983: TI-Raleigh
     ↓ Split (1983-12)
     1984-1989: Kwantum-Decosol
     → Name change (1990-01)
     1990-1996: Panasonic
     ↓ Merged with... (1996-06)
     1996-2003: Rabobank
     [etc.]
     ```
   - **Current Status**: Active / Defunct (year)
   - **Statistics**: Total years active, # of incarnations, # of sponsor changes
   - **Notable Achievements**: (if data available)
   - **Close Button**: X in top-right

3. **URL Update**: Add lineage ID to URL hash (#lineage=L_RALEIGH)
   - Allows direct linking to lineage view
   - Browser back button works

**Click on Sponsor Name/Bar**:
1. **Visual Changes**:
   - Highlight all bars featuring this sponsor (strong glow)
   - Hide/fade all teams never associated with this sponsor
   - Show connection lines between different teams with same sponsor
   - Display sponsor "journey" through teams

2. **Sidebar Panel Opens**:
   - **Header**: Sponsor brand name + logo (if available)
   - **Company Info**: Parent company, country, industry
   - **Sponsorship History**: Chronological list:
     ```
     2010-2015: Team Sky (Title Primary)
     2016-2018: Team Sky (Title Primary)
     2019-2020: Team Ineos (Title Primary)
     2021-2023: Ineos Grenadiers (Title Primary)
     2024-2025: Ineos TotalEnergies (Title Secondary)
     ```
   - **Brand History**: Name changes (if any)
   - **Statistics**: Total years in cycling, # of teams sponsored
   - **Close Button**

**Click on Connection Line**:
- **Zoom Focus**: Pan and zoom to center on connection
- **Display Details**: Popup/modal with:
  - Succession type
  - Date
  - Confidence score
  - Staff transfer percentage (if known)
  - Source references (clickable links)
  - Notes/context
  - "Edit" button (if admin logged in)

**Click on Background** (outside any element):
- Clear all highlights
- Close sidebar panel
- Return to normal view
- Reset URL hash

#### 5.3.3 Multi-Select Interactions

**Ctrl/Cmd + Click**:
- Add teams to selection (multiple lineages)
- Highlight all selected lineages
- Sidebar shows combined information
- "Compare" mode with side-by-side stats

**Shift + Click** (two teams):
- Highlight shortest path between two teams
- Show succession chain connecting them
- Sidebar shows "Connection Path" information

### 5.4 Visual Feedback & States

#### 5.4.1 Loading States
- Initial load: Full-page spinner with progress indicator
- Data refresh: Subtle top-bar progress indicator
- Zooming: Immediate response, load details progressively
- Large dataset: "Loading more teams..." message

#### 5.4.2 Empty States
- No search results: "No teams found matching '[query]'"
- No teams in filter: "No teams in selected tiers for this period"
- No data: "Data not available for this period"

#### 5.4.3 Error States
- Failed to load: Error message with retry button
- Invalid date range: Red border on input, tooltip message
- Connection lost: Banner notification with auto-retry

#### 5.4.4 Success States
- Data saved: Green checkmark animation
- Filter applied: "Showing X teams" counter update
- Search complete: Results count + highlight

### 5.5 Responsive Design

#### 5.5.1 Desktop (>1200px)
- Full visualization with all controls
- Sidebar panel 400px
- Time range selector always visible

#### 5.5.2 Tablet (768px - 1200px)
- Compact control panel
- Sidebar panel 300px (slides over content)
- Touch-optimized zoom/pan
- Simplified tooltips

#### 5.5.3 Mobile (< 768px)
- Vertical scrolling priority
- Full-screen visualization
- Bottom sheet for details (instead of sidebar)
- Simplified interactions (no hover, tap only)
- Hamburger menu for filters
- Single-team view emphasized

### 5.6 Accessibility

#### 5.6.1 Keyboard Navigation
- Tab: Navigate through interactive elements
- Enter/Space: Activate selected element
- Arrow keys: Pan viewport
- +/-: Zoom in/out
- Escape: Close panels, clear selection
- ?: Show keyboard shortcuts help

#### 5.6.2 Screen Reader Support
- ARIA labels on all interactive elements
- Live region announcements for state changes
- Alt text for visual elements
- Semantic HTML structure
- Skip navigation links

#### 5.6.3 Visual Accessibility
- WCAG AA contrast compliance
- Colorblind-safe palette option
- Pattern fills option (in addition to colors)
- Font size scaling (user preference)
- High contrast mode support
- Reduced motion option (disable animations)

---

## 6. Backend / CMS Architecture

### 6.1 Manual Data Management Interface

The backend Content Management System (CMS) provides administrative tools for data curation, conflict resolution, and manual overrides.

#### 6.1.1 Dashboard Overview
Landing page after login showing:
- Pending conflicts count (red badge)
- Recent changes log (last 20 entries)
- Data coverage statistics:
  - Total teams tracked
  - Total lineages defined
  - Total sponsors tracked
  - Date range coverage
  - Missing data percentage by decade
- Quick action buttons:
  - Create New Team
  - Create New Sponsor
  - Review Conflicts
  - Run Scraper
- System health indicators:
  - Last successful scrape timestamp
  - Database size
  - API status

### 6.2 Core Management Views

#### 6.2.1 Team Entity Editor

**List View**:
- Sortable/filterable table of all Team_Entity records
- Columns: Entity ID, Lineage, Name, Start Date, End Date, Tier, Country
- Search/filter by any column
- Actions: Edit, Delete, View Lineage, Duplicate
- Pagination (50 per page)
- Export button (CSV/JSON)

**Form View** (Create/Edit):
```
─────────────────────────────────────────
  TEAM ENTITY EDITOR
─────────────────────────────────────────
  Entity ID: [Auto-generated] or [____]
  Lineage ID: [Dropdown: Select or Create New]
  
  ┌─ Time Period ────────────────────────┐
  │ Start Date: [YYYY-MM-DD] [Calendar]  │
  │ End Date:   [YYYY-MM-DD] [Calendar]  │
  │             ☑ Currently Active        │
  └────────────────────────────────────────┘
  
  [Save] [Cancel] [Save & Add Another]
─────────────────────────────────────────
```

Below form: **Property Management Panel**
```
┌─ Properties for this Entity ───────────┐
│ [+Add Property]                         │
│                                         │
│ Property Type: NAME                     │
│ Value: Team Sky                         │
│ Start: 2010-01-01 | End: 2018-12-31    │
│ [Edit] [Delete]                         │
│                                         │
│ Property Type: UCI_CODE                 │
│ Value: SKY                              │
│ Start: 2012-01-01 | End: 2018-12-31    │
│ [Edit] [Delete]                         │
│                                         │
│ [Show More...]                          │
└───────────────────────────────────────────┘
```

**Property Quick-Add Modal**:
```
┌─ Add Property ──────────────────────────┐
│ Type: [NAME ▼]                          │
│       NAME                              │
│       UCI_CODE                          │
│       TIER                              │
│       NATIONALITY                       │
│       OWNER                             │
│                                         │
│ Value: [_____________________]          │
│                                         │
│ Start Date: [YYYY-MM-DD] [Calendar]    │
│ End Date:   [YYYY-MM-DD] [Calendar]    │
│             ☐ Currently Active          │
│                                         │
│ Confidence: [0.95____] (0.0 - 1.0)     │
│                                         │
│ Sources: [+Add Source]                  │
│ • procyclingstats.com/team/sky         │
│   [Remove]                              │
│                                         │
│ Notes: [________________________]       │
│        [________________________]       │
│                                         │
│ [Save Property] [Cancel]                │
└───────────────────────────────────────────┘
```

#### 6.2.2 Lineage Editor

**Lineage Detail View**:
```
─────────────────────────────────────────
  LINEAGE: Raleigh / TI-Raleigh / Panasonic
  ID: L_RALEIGH_001
─────────────────────────────────────────
  Primary Name: TI-Raleigh
  Founded: ~1972
  Status: Defunct (1996)
  
  [Edit Metadata] [Delete Lineage] [View Timeline]
  
┌─ Team Entities in this Lineage ────────┐
│                                         │
│ 1972-01-01 to 1983-12-31               │
│ TI-Raleigh (Original)                   │
│ [View] [Edit]                           │
│ ↓ Split into 2 teams (1983-12)         │
│                                         │
│ 1984-01-01 to 1989-12-31               │
│ Kwantum-Decosol                         │
│ [View] [Edit]                           │
│ → Name change (1990-01)                 │
│                                         │
│ 1990-01-01 to 1996-06-30               │
│ Panasonic                               │
│ [View] [Edit]                           │
│ ↓ Merged with Rabobank (1996-06)       │
│                                         │
│ [+Add Entity to Lineage]                │
└───────────────────────────────────────────┘

┌─ Succession Links ──────────────────────┐
│                                         │
│ OUTGOING:                               │
│ → Kwantum-Decosol (L_KWANTUM_001)      │
│   Type: SPLIT_EQUAL                     │
│   Date: 1983-12                         │
│   [View] [Edit] [Remove]                │
│                                         │
│ → Panasonic Team (L_PANASONIC_001)     │
│   Type: SPLIT_EQUAL                     │
│   Date: 1983-12                         │
│   [View] [Edit] [Remove]                │
│                                         │
│ INCOMING:                               │
│ (None - original founding)              │
│                                         │
│ [+Add Succession Link]                  │
└───────────────────────────────────────────┘
```

**Succession Link Editor** (Modal/Form):
```
┌─ Create/Edit Succession Link ──────────┐
│                                         │
│ Source Entity: [TI-Raleigh_1983_Entity] │
│ Target Entity: [Search/Select...▼]     │
│                                         │
│ Link Type: [SPLIT_EQUAL ▼]             │
│   • DIRECT_CONTINUATION                 │
│   • LICENSE_SALE                        │
│   • QUALIFIED_SUCCESSION                │
│   • SPLIT_EQUAL                         │
│   • SPLIT_MAJOR_MINOR                   │
│   • PARTIAL_SPLIT                       │
│   • MERGE_EQUAL                         │
│   • ACQUISITION                         │
│   • NEW_LINEAGE                         │
│                                         │
│ Qualifier: [None ▼] (optional)          │
│                                         │
│ Transition Date: [1983-12] (YYYY-MM)   │
│                                         │
│ Staff Transfer %: [50___] (0-100)      │
│                                         │
│ Confidence: [0.85____] (0.0-1.0)       │
│                                         │
│ Sources (multiple): [+Add]              │
│ • en.wikipedia.org/wiki/TI-Raleigh     │
│   [Remove]                              │
│ • procyclingstats.com/team/ti-raleigh  │
│   [Remove]                              │
│                                         │
│ Notes / Context:                        │
│ [_________________________________]     │
│ [_________________________________]     │
│                                         │
│ ☑ Manual Override (I verified this)    │
│                                         │
│ [Save Link] [Cancel]                    │
└───────────────────────────────────────────┘
```

#### 6.2.3 Sponsor Management

**Sponsor Master List**:
- Table view of all Sponsor_Master records
- Search by name, parent company, country
- Actions: Edit, Delete, View History, Merge Duplicates

**Sponsor Detail View**:
```
─────────────────────────────────────────
  SPONSOR: Soudal
  ID: S_SOUDAL_001
─────────────────────────────────────────
  Legal Name: Soudal Holding
  Parent Company: Soudal Group
  Country: Belgium
  Industry: Chemical Manufacturing
  Website: soudal.com
  
  [Edit] [Delete] [View Teams]
  
┌─ Brand Names Used ──────────────────────┐
│                                         │
│ Soudal (1990-present)                   │
│ ☑ Primary Brand                         │
│ [Edit Dates]                            │
│                                         │
│ [+Add Brand Name]                       │
└───────────────────────────────────────────┘

┌─ Sponsorship History ───────────────────┐
│                                         │
│ 2021-2024: Lotto-Soudal                 │
│ Rank: TITLE_PRIMARY                     │
│ [View Team] [Edit]                      │
│                                         │
│ 2025-present: Soudal Quick-Step         │
│ Rank: TITLE_SECONDARY                   │
│ [View Team] [Edit]                      │
│                                         │
│ [Show Full History]                     │
└───────────────────────────────────────────┘
```

**Team-Sponsor Link Editor**:
```
┌─ Add/Edit Sponsorship ──────────────────┐
│                                         │
│ Team Entity: [QuickStep_2025_Entity]    │
│ Sponsor Brand: [Soudal ▼]              │
│                                         │
│ Sponsor Rank: [TITLE_SECONDARY ▼]      │
│   • TITLE_PRIMARY                       │
│   • TITLE_SECONDARY                     │
│   • TITLE_TERTIARY                      │
│   • MAJOR                               │
│   • BIKE                                │
│   • APPAREL                             │
│   • HELMET                              │
│   • MINOR                               │
│                                         │
│ Display Order: [2_] (for title sponsors)│
│                                         │
│ Start Date: [2025-01-01] [Calendar]    │
│ End Date:   [________] [Calendar]       │
│             ☑ Currently Active          │
│                                         │
│ Confidence: [0.95____]                  │
│                                         │
│ Sources: [+Add]                         │
│                                         │
│ [Save] [Cancel]                         │
└───────────────────────────────────────────┘
```

### 6.3 Conflict Resolution Dashboard

**Conflict Queue View**:
```
─────────────────────────────────────────
  CONFLICT RESOLUTION DASHBOARD
─────────────────────────────────────────
  
  Status Filter: [All ▼] [PENDING ▼] [UNDER_REVIEW ▼]
  Type Filter:   [All ▼] [DATE_MISMATCH ▼] ...
  Sort by:       [Created Date ▼] [Priority ▼]
  
  Search: [__________________] [Search]
  
  Showing 15 pending conflicts
  
┌─────────────────────────────────────────┐
│ ⚠️ DATE_MISMATCH | High Priority         │
│ Team: Team Sky                          │
│ Field: End Date                         │
│ Created: 2024-11-10 14:32               │
│                                         │
│ ProCyclingStats: 2018-12-31             │
│ Wikipedia (EN): 2019-01-01              │
│ Wikipedia (FR): 2018-12-31              │
│                                         │
│ [Review & Resolve]                      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ⚠️ LINEAGE_DISAGREEMENT | Medium        │
│ Team: Liberty Seguros → Astana          │
│ Field: Succession Type                  │
│ Created: 2024-11-09 09:15               │
│                                         │
│ [Review & Resolve]                      │
└─────────────────────────────────────────┘

  [Load More...]
  
─────────────────────────────────────────
```

**Conflict Resolution Interface**:
```
┌─ RESOLVE CONFLICT ──────────────────────┐
│                                         │
│ Team: Team Sky (T_SKY_2010)             │
│ Field: end_date                         │
│ Conflict Type: DATE_MISMATCH            │
│                                         │
│ ┌─ Conflicting Values ─────────────────┐│
│ │                                       ││
│ │ ○ 2018-12-31                          ││
│ │   Sources: ProCyclingStats (1.0),    ││
│ │            Wikipedia FR (0.85)        ││
│ │   Total Weight: 1.85                  ││
│ │                                       ││
│ │ ○ 2019-01-01                          ││
│ │   Sources: Wikipedia EN (0.85)       ││
│ │   Total Weight: 0.85                  ││
│ │                                       ││
│ │ ○ Custom Value: [____-__-__]         ││
│ │                                       ││
│ └───────────────────────────────────────┘│
│                                         │
│ ┌─ Context / Evidence ─────────────────┐│
│ │ From Wikipedia EN article:           ││
│ │ "The team was disbanded at the end   ││
│ │ of the 2018 season, with the final   ││
│ │ race on December 31, 2018..."        ││
│ │                                       ││
│ │ From ProCyclingStats:                ││
│ │ Last race listed: 2018-12-31         ││
│ │ [View Full Context]                  ││
│ └───────────────────────────────────────┘│
│                                         │
│ Resolution Reason:                      │
│ [_________________________________]     │
│ [_________________________________]     │
│                                         │
│ Resolution Method:                      │
│ [GOLD_STANDARD ▼]                       │
│   • GOLD_STANDARD                       │
│   • WIKIPEDIA_MAJORITY                  │
│   • MANUAL_DECISION                     │
│   • CUSTOM_VALUE                        │
│                                         │
│ [Resolve & Apply] [Defer] [Cancel]      │
│                                         │
│ ☑ Keep original conflict data for audit│
└───────────────────────────────────────────┘
```

**After Resolution**:
- Conflict record updated with:
  - resolved_value
  - resolution_method
  - resolution_reason
  - resolved_by (user)
  - resolved_at (timestamp)
  - status = RESOLVED_MANUAL
- Audit_Log entry created
- Related data records updated
- User returned to queue (or next conflict if batch mode)

#### 6.3.1 Batch Conflict Resolution
For similar conflicts (same type, same team):
- "Apply to Similar" button
- Shows count of similar conflicts
- Allows applying same resolution logic to multiple conflicts
- Individual review option for each

### 6.4 Audit & History System

#### 6.4.1 Audit Log Viewer
```
─────────────────────────────────────────
  AUDIT LOG
─────────────────────────────────────────
  
  Date Range: [2024-11-01] to [2024-11-14]
  User: [All ▼]
  Action: [All ▼] [INSERT ▼] [UPDATE ▼] ...
  Table: [All ▼]
  
  Search: [__________________] [Search]
  
  [Export Log] [Clear Filters]
  
┌─────────────────────────────────────────┐
│ 2024-11-14 10:23:15                     │
│ User: admin@example.com                 │
│ Action: CONFLICT_RESOLVED               │
│                                         │
│ Table: Team_Property_Link               │
│ Record: TPL_12345                       │
│ Field: end_date                         │
│ Old: NULL                               │
│ New: 2018-12-31                         │
│                                         │
│ Reason: "Resolved based on PCS priority"│
│ Related Conflict: CNF_67890             │
│                                         │
│ [View Details] [Revert]                 │
└─────────────────────────────────────────┘

  Showing 1-50 of 234 entries
  [Previous] [1] [2] [3] [4] [5] [Next]
  
─────────────────────────────────────────
```

#### 6.4.2 Version History (Per Record)
On any entity detail page:
```
┌─ Change History ────────────────────────┐
│                                         │
│ 5 changes to this record                │
│ [Show Full History]                     │
│                                         │
│ 2024-11-14 10:23 by admin               │
│ • end_date: NULL → 2018-12-31          │
│                                         │
│ 2024-11-10 15:30 by admin               │
│ • confidence_score: 0.8 → 0.95         │
│                                         │
│ 2024-11-09 09:00 by scraper_bot        │
│ • Record created                        │
│                                         │
│ [View All] [Compare Versions]           │
└───────────────────────────────────────────┘
```

**Version Compare View**:
- Side-by-side diff of any two versions
- Highlight changes (additions in green, deletions in red)
- Option to restore previous version
- Requires confirmation for restoration

### 6.5 Data Import/Export

#### 6.5.1 Bulk Import Interface
```
─────────────────────────────────────────
  BULK DATA IMPORT
─────────────────────────────────────────
  
  Import Type: [Team Entities ▼]
               • Team Entities
               • Sponsors
               • Team Properties
               • Succession Links
               • Team-Sponsor Links
  
  File Format: [CSV ▼] [JSON ▼]
  
  Upload File: [Choose File] [team_data.csv]
  
  ┌─ Preview (First 5 rows) ────────────┐
  │ entity_id | lineage_id | start_date │
  │ T_001     | L_001      | 1972-01-01 │
  │ T_002     | L_001      | 1984-01-01 │
  │ ...                                  │
  └────────────────────────────────────────┘
  
  Options:
  ☑ Validate data before import
  ☑ Stop on first error
  ☐ Update existing records (if ID matches)
  ☑ Create audit log entries
  
  [Import] [Cancel]
  
─────────────────────────────────────────
```

**Import Process**:
1. File upload and parsing
2. Schema validation
3. Data type checking
4. Conflict detection (duplicate IDs, date overlaps)
5. Preview conflicts/warnings
6. User confirms
7. Execute import
8. Show results summary (X created, Y updated, Z errors)
9. Download error log (if any)

#### 6.5.2 Export Interface
```
─────────────────────────────────────────
  DATA EXPORT
─────────────────────────────────────────
  
  Export Type: [Full Database ▼]
               • Full Database
               • Team Entities Only
               • Sponsors Only
               • Specific Lineage
               • Custom Query
  
  Format: [JSON ▼] [CSV ▼] [SQL Dump ▼]
  
  Date Range: [All Time ▼]
  Include: ☑ Deleted records
           ☑ Audit logs
           ☑ Conflict data
  
  [Generate Export] [Schedule Recurring]
  
─────────────────────────────────────────
```

### 6.6 Scraper Management

#### 6.6.1 Scraper Dashboard
```
─────────────────────────────────────────
  WEB SCRAPER CONTROL PANEL
─────────────────────────────────────────
  
  Last Run: 2024-11-13 02:00:00 (1 day ago)
  Status: ✓ Completed Successfully
  Duration: 2h 34m
  Records Updated: 145
  New Conflicts: 8
  
  Next Scheduled Run: 2024-11-20 02:00:00
  
  [Run Now] [Configure Schedule] [View Logs]
  
┌─ Data Sources ──────────────────────────┐
│                                         │
│ ✓ ProCyclingStats                       │
│   Last: 2024-11-13 | Status: Success    │
│   Records: 1,234                        │
│   [Enable] [Test] [Configure]           │
│                                         │
│ ✓ Wikipedia (EN)                        │
│   Last: 2024-11-13 | Status: Success    │
│   Records: 987                          │
│   [Enable] [Test] [Configure]           │
│                                         │
│ ✓ Wikipedia (DE)                        │
│   Last: 2024-11-13 | Status: Success    │
│   Records: 856                          │
│   [Enable] [Test] [Configure]           │
│                                         │
│ ⚠ FirstCycling                          │
│   Last: 2024-11-13 | Status: Partial    │
│   Records: 543 | Errors: 12             │
│   [Enable] [Test] [Configure]           │
│                                         │
│ [Show All Sources (7 total)]            │
└───────────────────────────────────────────┘

┌─ Scraping Rules ────────────────────────┐
│                                         │
│ Auto-resolve conflicts: ☑ Enabled       │
│ Minimum confidence: [0.85___]           │
│ Rate limiting: [5__] requests/second    │
│ User agent: [Custom ▼]                  │
│ Respect robots.txt: ☑ Yes               │
│                                         │
│ [Save Settings]                         │
└───────────────────────────────────────────┘
```

#### 6.6.2 Source Configuration
```
┌─ Configure: ProCyclingStats ────────────┐
│                                         │
│ Base URL: procyclingstats.com          │
│ Enabled: ☑ Yes                          │
│ Priority: [1_] (1=highest)              │
│ Reliability: [1.0___] (0.0-1.0)        │
│                                         │
│ ┌─ Scraping Targets ─────────────────┐ │
│ │ ☑ Team list pages                   │ │
│ │ ☑ Individual team pages             │ │
│ │ ☑ Roster pages                      │ │
│ │ ☐ Race results (future use)         │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Rate Limit: [3_] requests/second        │
│ Retry on Error: ☑ Yes (max 3 attempts) │
│ Timeout: [30__] seconds                 │
│                                         │
│ Custom Headers:                         │
│ User-Agent: [CyclingTimeline/1.0]      │
│ From: [admin@example.com]               │
│                                         │
│ [Test Connection] [Save] [Cancel]       │
└───────────────────────────────────────────┘
```

#### 6.6.3 Scraper Logs
```
─────────────────────────────────────────
  SCRAPER EXECUTION LOG
─────────────────────────────────────────
  
  Run ID: SCR_20241113_020000
  Started: 2024-11-13 02:00:00
  Completed: 2024-11-13 04:34:15
  Status: SUCCESS
  
┌─ Summary ───────────────────────────────┐
│ Sources Scraped: 7                      │
│ Pages Fetched: 1,247                    │
│ Records Found: 3,245                    │
│ Records Updated: 145                    │
│ Records Created: 23                     │
│ Conflicts Detected: 8                   │
│ Errors: 12 (non-critical)               │
└───────────────────────────────────────────┘

┌─ Source Breakdown ──────────────────────┐
│                                         │
│ ProCyclingStats: ✓ Success              │
│ • Pages: 456 | Records: 1,234           │
│ • Updated: 67 | New: 12                 │
│                                         │
│ Wikipedia EN: ✓ Success                 │
│ • Pages: 234 | Records: 987             │
│ • Updated: 34 | New: 5                  │
│                                         │
│ [Show All]                              │
└───────────────────────────────────────────┘

┌─ Errors (12 non-critical) ──────────────┐
│                                         │
│ ⚠ FirstCycling: 404 Not Found           │
│   URL: firstcycling.com/team-123        │
│   Action: Skipped                       │
│                                         │
│ ⚠ Wikipedia DE: Parse Error              │
│   Page: Team_XYZ                        │
│   Issue: Infobox format changed         │
│   Action: Flagged for manual review     │
│                                         │
│ [Show All Errors]                       │
└───────────────────────────────────────────┘

  [Download Full Log] [Re-run Failed Items]
  
─────────────────────────────────────────
```

### 6.7 User Management (Optional Future Feature)

#### 6.7.1 Basic Authentication
- Username/password login
- Session management
- Password reset functionality

#### 6.7.2 Role-Based Access Control (RBAC)
**Roles**:
- `ADMIN`: Full access to all features
- `CURATOR`: Can edit data, resolve conflicts, manage entities
- `VIEWER`: Read-only access to backend
- `SCRAPER`: Service account for automated scraping

**Permissions Matrix**:
| Action | Admin | Curator | Viewer | Scraper |
|--------|-------|---------|--------|---------|
| View data | ✓ | ✓ | ✓ | ✗ |
| Edit entities | ✓ | ✓ | ✗ | ✗ |
| Resolve conflicts | ✓ | ✓ | ✗ | ✗ |
| Delete records | ✓ | ✗ | ✗ | ✗ |
| Manage users | ✓ | ✗ | ✗ | ✗ |
| Run scraper | ✓ | ✓ | ✗ | ✓ |
| View audit logs | ✓ | ✓ | ✓ | ✗ |
| Export data | ✓ | ✓ | ✓ | ✗ |

---

## 7. Technical Architecture

### 7.1 Technology Stack Recommendations

#### 7.1.1 Frontend
**Primary Technology**: Modern JavaScript framework with strong SVG/Canvas support

**Recommended Options**:
1. **React + D3.js** (Recommended)
   - React for UI components and state management
   - D3.js for complex data visualization
   - React-Router for navigation
   - Pros: Large ecosystem, excellent for complex interactions
   - Cons: Steeper learning curve

2. **Vue.js + D3.js** (Alternative)
   - Vue for UI components
   - D3.js for visualization
   - Vue-Router for navigation
   - Pros: Simpler than React, good documentation
   - Cons: Smaller ecosystem

3. **Vanilla JavaScript + D3.js** (Simplest)
   - Pure HTML/CSS/JS
   - D3.js for visualization
   - Pros: No build process, maximum simplicity
   - Cons: More code for complex interactions

**Supporting Libraries**:
- **D3.js**: Core visualization library for Sankey network
- **date-fns** or **Luxon**: Date manipulation
- **Axios** or **Fetch API**: HTTP requests
- **Lodash**: Utility functions (if needed)

**Build Tools** (if using framework):
- **Vite** or **Webpack**: Module bundling
- **Babel**: JavaScript transpilation
- **PostCSS**: CSS processing
- **ESLint**: Code linting

#### 7.1.2 Backend
**Primary Technology**: Python-based web framework

**Recommended Options**:
1. **Flask** (Recommended for simplicity)
   - Lightweight Python web framework
   - Easy to learn and extend
   - RESTful API development
   - Pros: Simple, flexible, well-documented
   - Cons: Fewer built-in features than Django

2. **FastAPI** (Alternative - modern)
   - Fast, modern Python framework
   - Automatic API documentation (OpenAPI)
   - Type hints and validation
   - Pros: Fast, automatic validation, great docs
   - Cons: Relatively newer

3. **Django** (Alternative - full-featured)
   - Full-featured web framework
   - Built-in admin panel
   - ORM included
   - Pros: Batteries included, robust
   - Cons: More complex, heavier

**Supporting Libraries**:
- **SQLAlchemy**: Database ORM (if using Flask/FastAPI)
- **Alembic**: Database migrations
- **Beautiful Soup 4**: HTML parsing
- **Scrapy** or **Requests**: Web scraping
- **APScheduler**: Task scheduling
- **Flask-CORS** or **FastAPI CORS**: Cross-origin requests
- **python-dotenv**: Environment configuration

#### 7.1.3 Database
**Recommended Option 1: PostgreSQL** (Relational - Recommended)
- **Pros**:
  - Excellent for complex relational data
  - JSONB support for flexible fields
  - Strong data integrity (foreign keys, constraints)
  - Mature, reliable, well-documented
  - Good for temporal data (date ranges)
  - PostGIS extension for future geographic features
- **Cons**:
  - Requires PostgreSQL server setup
  - More complex than SQLite

**Recommended Option 2: SQLite** (Relational - Simpler)
- **Pros**:
  - Zero configuration
  - File-based (perfect for local development)
  - Supports most SQL features
  - Very simple deployment
- **Cons**:
  - Limited concurrency
  - Not ideal for heavy write loads
  - Size limitations for very large datasets

**Alternative: Neo4j** (Graph Database)
- **Pros**:
  - Perfect for network/graph relationships
  - Excellent for traversing lineage connections
  - Built-in graph algorithms
  - Cypher query language for paths
- **Cons**:
  - Steeper learning curve
  - Additional infrastructure
  - Less familiar to most developers

**Recommendation**: Start with **PostgreSQL** for production or **SQLite** for initial local development. The relational model matches the defined schema well, and both support the necessary features.

#### 7.1.4 Deployment
**Local Development**:
- **Frontend**: Local dev server (Vite/Webpack)
- **Backend**: Flask/FastAPI dev server
- **Database**: SQLite file or local PostgreSQL

**Production Options** (for future hosting):
- **Frontend**: 
  - Static file hosting (Netlify, Vercel, GitHub Pages)
  - CDN for performance
- **Backend**:
  - VPS (DigitalOcean, Linode)
  - PaaS (Heroku, Railway, Render)
  - Docker container
- **Database**:
  - Managed PostgreSQL (AWS RDS, DigitalOcean Managed DB)
  - Self-hosted on VPS

### 7.2 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     USER BROWSER                        │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Frontend Application (React/Vue)          │ │
│  │                                                   │ │
│  │  ├─ Visualization Layer (D3.js Sankey)           │ │
│  │  ├─ Interaction Controller                       │ │
│  │  ├─ State Management                             │ │
│  │  └─ API Client                                   │ │
│  └───────────────────────────────────────────────────┘ │
│                          ↕ HTTPS/JSON                   │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│                   BACKEND SERVER                        │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Web Framework (Flask/FastAPI)             │ │
│  │                                                   │ │
│  │  ├─ RESTful API Endpoints                        │ │
│  │  ├─ CMS Views & Controllers                      │ │
│  │  ├─ Authentication & Authorization               │ │
│  │  └─ Request/Response Handling                    │ │
│  └───────────────────────────────────────────────────┘ │
│                          ↕                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │           Business Logic Layer                    │ │
│  │                                                   │ │
│  │  ├─ Data Aggregation Service                     │ │
│  │  ├─ Conflict Resolution Engine                   │ │
│  │  ├─ Lineage Calculation Service                  │ │
│  │  ├─ Color Assignment Service                     │ │
│  │  └─ Export/Import Service                        │ │
│  └───────────────────────────────────────────────────┘ │
│                          ↕                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │             Data Access Layer (ORM)               │ │
│  │                                                   │ │
│  │  ├─ Entity Models                                │ │
│  │  ├─ Query Builders                               │ │
│  │  └─ Transaction Management                       │ │
│  └───────────────────────────────────────────────────┘ │
│                          ↕                              │
└─────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────┐
│              DATABASE (PostgreSQL/SQLite)               │
│                                                         │
│  ├─ Team_Entity                                        │
│  ├─ Team_Lineage                                       │
│  ├─ Team_Property_Link                                 │
│  ├─ Sponsor_Master                                     │
│  ├─ Sponsor_Brand_History                              │
│  ├─ Team_Sponsor_Link                                  │
│  ├─ Team_Succession_Link                               │
│  ├─ UCI_Tier_Definition                                │
│  ├─ UCI_Tier_Label_History                             │
│  ├─ Data_Source                                        │
│  ├─ Data_Conflict                                      │
│  ├─ Audit_Log                                          │
│  └─ Color_Scheme                                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              SCRAPING SERVICE (Async)                   │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │            Scraper Orchestrator                   │ │
│  │                                                   │ │
│  │  ├─ Scheduler (APScheduler)                      │ │
│  │  ├─ Source Managers                              │ │
│  │  │  ├─ ProCyclingStats Scraper                   │ │
│  │  │  ├─ Wikipedia Scraper (multi-language)        │ │
│  │  │  ├─ FirstCycling Scraper                      │ │
│  │  │  └─ Other Source Scrapers                     │ │
│  │  ├─ HTML Parser (BeautifulSoup/Scrapy)           │ │
│  │  ├─ Data Normalizer                              │ │
│  │  ├─ Conflict Detector                            │ │
│  │  └─ Database Writer                              │ │
│  └───────────────────────────────────────────────────┘ │
│                          ↕                              │
│                     Database                            │
└─────────────────────────────────────────────────────────┘
```

### 7.3 API Design

#### 7.3.1 RESTful API Endpoints

**Teams & Entities**:
```
GET    /api/teams                    # List all team entities (paginated, filtered)
GET    /api/teams/:id                # Get specific team entity
POST   /api/teams                    # Create new team entity
PUT    /api/teams/:id                # Update team entity
DELETE /api/teams/:id                # Delete team entity

GET    /api/teams/:id/properties     # Get all properties for a team
POST   /api/teams/:id/properties     # Add property to team
PUT    /api/properties/:id           # Update specific property
DELETE /api/properties/:id           # Delete property

GET    /api/teams/:id/sponsors       # Get sponsors for a team
POST   /api/teams/:id/sponsors       # Link sponsor to team
DELETE /api/team-sponsors/:id        # Remove sponsor link
```

**Lineages**:
```
GET    /api/lineages                 # List all lineages
GET    /api/lineages/:id             # Get lineage details
POST   /api/lineages                 # Create new lineage
PUT    /api/lineages/:id             # Update lineage
DELETE /api/lineages/:id             # Delete lineage

GET    /api/lineages/:id/timeline    # Get full timeline for lineage
GET    /api/lineages/:id/succession  # Get succession links
POST   /api/lineages/:id/succession  # Create succession link
PUT    /api/succession-links/:id     # Update succession link
DELETE /api/succession-links/:id     # Delete succession link
```

**Sponsors**:
```
GET    /api/sponsors                 # List all sponsors
GET    /api/sponsors/:id             # Get sponsor details
POST   /api/sponsors                 # Create new sponsor
PUT    /api/sponsors/:id             # Update sponsor
DELETE /api/sponsors/:id             # Delete sponsor

GET    /api/sponsors/:id/brands      # Get brand history
POST   /api/sponsors/:id/brands      # Add brand name
PUT    /api/brands/:id               # Update brand
DELETE /api/brands/:id               # Delete brand

GET    /api/sponsors/:id/teams       # Get teams sponsored
```

**Visualization Data**:
```
GET    /api/timeline                 # Get full timeline data
  ?start_year=2010
  &end_year=2020
  &tiers=T1,T2
  &lineages=L_001,L_002
  
GET    /api/timeline/sponsors/:id    # Get sponsor journey
GET    /api/timeline/lineages/:id    # Get lineage path
```

**Conflicts**:
```
GET    /api/conflicts                # List pending conflicts
  ?status=PENDING
  &type=DATE_MISMATCH
  
GET    /api/conflicts/:id            # Get conflict details
POST   /api/conflicts/:id/resolve    # Resolve conflict
DELETE /api/conflicts/:id            # Dismiss conflict
```

**Scraper**:
```
GET    /api/scraper/status           # Get scraper status
POST   /api/scraper/run              # Trigger scrape
GET    /api/scraper/logs             # Get scraper logs
GET    /api/scraper/sources          # List data sources
PUT    /api/scraper/sources/:id      # Update source config
```

**Audit**:
```
GET    /api/audit-log                # Get audit log entries
  ?start_date=2024-01-01
  &end_date=2024-12-31
  &user=admin
  &table=Team_Entity
  
GET    /api/audit-log/:record_type/:record_id  # Get history for specific record
```

#### 7.3.2 API Response Formats

**Success Response**:
```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "meta": {
    "timestamp": "2024-11-14T10:30:00Z",
    "request_id": "req_12345"
  }
}
```

**Error Response**:
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Start date cannot be after end date",
    "field": "start_date",
    "details": {}
  },
  "meta": {
    "timestamp": "2024-11-14T10:30:00Z",
    "request_id": "req_12345"
  }
}
```

**Paginated Response**:
```json
{
  "status": "success",
  "data": [ /* items */ ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 234,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "timestamp": "2024-11-14T10:30:00Z"
  }
}
```

### 7.4 Database Schema Implementation

#### 7.4.1 PostgreSQL Schema (SQL)
```sql
-- Core Tables

CREATE TABLE team_lineage (
    lineage_id VARCHAR(50) PRIMARY KEY,
    primary_name VARCHAR(255),
    founding_year INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE team_entity (
    entity_id VARCHAR(50) PRIMARY KEY,
    lineage_id VARCHAR(50) NOT NULL REFERENCES team_lineage(lineage_id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_date_range CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_team_entity_lineage ON team_entity(lineage_id);
CREATE INDEX idx_team_entity_dates ON team_entity(start_date, end_date);

CREATE TABLE team_property_link (
    property_id VARCHAR(50) PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL REFERENCES team_entity(entity_id) ON DELETE CASCADE,
    property_type VARCHAR(20) NOT NULL CHECK (property_type IN ('NAME', 'UCI_CODE', 'TIER', 'NATIONALITY', 'OWNER')),
    property_value TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    source_references JSONB,
    notes TEXT,
    CONSTRAINT valid_property_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_property_entity ON team_property_link(entity_id);
CREATE INDEX idx_property_type ON team_property_link(property_type);
CREATE INDEX idx_property_dates ON team_property_link(start_date, end_date);

-- Sponsor Tables

CREATE TABLE sponsor_master (
    sponsor_id VARCHAR(50) PRIMARY KEY,
    legal_name VARCHAR(255) NOT NULL,
    parent_company VARCHAR(255),
    country VARCHAR(2),
    industry_sector VARCHAR(100),
    website VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sponsor_brand_history (
    brand_id VARCHAR(50) PRIMARY KEY,
    sponsor_id VARCHAR(50) NOT NULL REFERENCES sponsor_master(sponsor_id) ON DELETE CASCADE,
    brand_name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    is_primary BOOLEAN DEFAULT FALSE,
    notes TEXT,
    CONSTRAINT valid_brand_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_brand_sponsor ON sponsor_brand_history(sponsor_id);
CREATE INDEX idx_brand_dates ON sponsor_brand_history(start_date, end_date);

CREATE TABLE team_sponsor_link (
    link_id VARCHAR(50) PRIMARY KEY,
    entity_id VARCHAR(50) NOT NULL REFERENCES team_entity(entity_id) ON DELETE CASCADE,
    brand_id VARCHAR(50) NOT NULL REFERENCES sponsor_brand_history(brand_id) ON DELETE CASCADE,
    sponsor_rank VARCHAR(20) NOT NULL CHECK (sponsor_rank IN ('TITLE_PRIMARY', 'TITLE_SECONDARY', 'TITLE_TERTIARY', 'MAJOR', 'BIKE', 'APPAREL', 'HELMET', 'MINOR', 'TECHNICAL', 'RESERVE_1', 'RESERVE_2', 'RESERVE_3', 'RESERVE_4', 'RESERVE_5')),
    display_order INTEGER,
    start_date DATE NOT NULL,
    end_date DATE,
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    source_references JSONB,
    CONSTRAINT valid_sponsor_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_sponsor_link_entity ON team_sponsor_link(entity_id);
CREATE INDEX idx_sponsor_link_brand ON team_sponsor_link(brand_id);
CREATE INDEX idx_sponsor_link_dates ON team_sponsor_link(start_date, end_date);

-- Succession Tables

CREATE TABLE team_succession_link (
    link_id VARCHAR(50) PRIMARY KEY,
    source_entity_id VARCHAR(50) NOT NULL REFERENCES team_entity(entity_id) ON DELETE CASCADE,
    target_entity_id VARCHAR(50) NOT NULL REFERENCES team_entity(entity_id) ON DELETE CASCADE,
    link_type VARCHAR(30) NOT NULL CHECK (link_type IN ('DIRECT_CONTINUATION', 'LICENSE_SALE', 'QUALIFIED_SUCCESSION', 'SPLIT_EQUAL', 'SPLIT_MAJOR_MINOR', 'PARTIAL_SPLIT', 'MERGE_EQUAL', 'ACQUISITION', 'NEW_LINEAGE')),
    link_qualifier VARCHAR(30) CHECK (link_qualifier IN ('MAJOR_PORTION', 'MINOR_PORTION', 'PARTIAL_STAFF', 'LICENSE_ONLY', 'SPONSOR_DRIVEN')),
    transition_date DATE NOT NULL,
    staff_transfer_percentage INTEGER CHECK (staff_transfer_percentage BETWEEN 0 AND 100),
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    source_references JSONB NOT NULL,
    notes TEXT,
    manual_override BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT no_self_link CHECK (source_entity_id != target_entity_id)
);

CREATE INDEX idx_succession_source ON team_succession_link(source_entity_id);
CREATE INDEX idx_succession_target ON team_succession_link(target_entity_id);
CREATE INDEX idx_succession_type ON team_succession_link(link_type);

-- UCI Tier Tables

CREATE TABLE uci_tier_definition (
    tier_id VARCHAR(10) PRIMARY KEY,
    tier_level INTEGER NOT NULL UNIQUE,
    description TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE uci_tier_label_history (
    label_id VARCHAR(50) PRIMARY KEY,
    tier_id VARCHAR(10) NOT NULL REFERENCES uci_tier_definition(tier_id) ON DELETE CASCADE,
    official_label VARCHAR(100) NOT NULL,
    start_year INTEGER NOT NULL,
    end_year INTEGER,
    region VARCHAR(50),
    CONSTRAINT valid_label_years CHECK (end_year IS NULL OR end_year >= start_year)
);

CREATE INDEX idx_tier_label ON uci_tier_label_history(tier_id);
CREATE INDEX idx_tier_years ON uci_tier_label_history(start_year, end_year);

-- Supporting Tables

CREATE TABLE data_source (
    source_id VARCHAR(50) PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('WIKIPEDIA', 'DATABASE', 'OFFICIAL', 'MANUAL')),
    base_url VARCHAR(255),
    language VARCHAR(10),
    reliability_score DECIMAL(3,2) CHECK (reliability_score BETWEEN 0 AND 1),
    priority_rank INTEGER NOT NULL,
    scraping_enabled BOOLEAN DEFAULT FALSE,
    last_scraped TIMESTAMP,
    notes TEXT
);

CREATE TABLE data_conflict (
    conflict_id VARCHAR(50) PRIMARY KEY,
    entity_id VARCHAR(50) REFERENCES team_entity(entity_id) ON DELETE CASCADE,
    conflict_type VARCHAR(30) NOT NULL CHECK (conflict_type IN ('DATE_MISMATCH', 'NAME_VARIATION', 'SPONSOR_CONFLICT', 'LINEAGE_DISAGREEMENT', 'TIER_MISMATCH', 'NATIONALITY_CONFLICT')),
    field_name VARCHAR(100) NOT NULL,
    conflicting_values JSONB NOT NULL,
    resolution_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (resolution_status IN ('PENDING', 'UNDER_REVIEW', 'RESOLVED_AUTO', 'RESOLVED_MANUAL', 'DEFERRED', 'ACKNOWLEDGED')),
    resolved_value TEXT,
    resolution_method VARCHAR(30) CHECK (resolution_method IN ('GOLD_STANDARD', 'WIKIPEDIA_MAJORITY', 'MANUAL_DECISION', 'CUSTOM_VALUE', 'SOURCE_PRIORITY')),
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conflict_entity ON data_conflict(entity_id);
CREATE INDEX idx_conflict_status ON data_conflict(resolution_status);
CREATE INDEX idx_conflict_type ON data_conflict(conflict_type);

CREATE TABLE audit_log (
    log_id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100),
    action_type VARCHAR(30) NOT NULL CHECK (action_type IN ('INSERT', 'UPDATE', 'DELETE', 'CONFLICT_RESOLVED', 'SCRAPE_UPDATE', 'BULK_IMPORT', 'MANUAL_OVERRIDE')),
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    related_conflict_id VARCHAR(50) REFERENCES data_conflict(conflict_id) ON DELETE SET NULL,
    ip_address VARCHAR(45)
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_user ON audit_log(user_id);

CREATE TABLE color_scheme (
    color_id VARCHAR(50) PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('SPONSOR_BRAND', 'TEAM_PERIOD')),
    entity_id VARCHAR(50) NOT NULL,
    primary_color VARCHAR(7) NOT NULL,  -- Hex color
    secondary_color VARCHAR(7),
    tertiary_color VARCHAR(7),
    start_date DATE NOT NULL,
    end_date DATE,
    source VARCHAR(255),
    notes TEXT,
    CONSTRAINT valid_color_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_color_entity ON color_scheme(entity_type, entity_id);
CREATE INDEX idx_color_dates ON color_scheme(start_date, end_date);

-- Triggers for updated_at

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER update_team_entity_updated_at
    BEFORE UPDATE ON team_entity
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

#### 7.4.2 Sample Data Insertion

```sql
-- Insert UCI Tiers
INSERT INTO uci_tier_definition (tier_id, tier_level, description) VALUES
('T1', 1, 'Top tier professional teams'),
('T2', 2, 'Second tier professional teams'),
('T3', 3, 'Continental level teams'),
('T4', 4, 'Amateur/regional teams');

-- Insert Tier Label History
INSERT INTO uci_tier_label_history (label_id, tier_id, official_label, start_year, end_year) VALUES
('TL_001', 'T1', 'UCI WorldTeam', 2019, NULL),
('TL_002', 'T1', 'WorldTour', 2011, 2018),
('TL_003', 'T1', 'UCI ProTeam', 2005, 2010),
('TL_004', 'T2', 'UCI ProTeam', 2019, NULL),
('TL_005', 'T2', 'Professional Continental', 2005, 2018);

-- Insert Data Sources
INSERT INTO data_source (source_id, source_name, source_type, base_url, priority_rank, reliability_score, scraping_enabled) VALUES
('SRC_PCS', 'ProCyclingStats', 'DATABASE', 'https://www.procyclingstats.com', 1, 1.0, TRUE),
('SRC_WIKI_EN', 'Wikipedia (English)', 'WIKIPEDIA', 'https://en.wikipedia.org', 2, 0.85, TRUE),
('SRC_WIKI_DE', 'Wikipedia (German)', 'WIKIPEDIA', 'https://de.wikipedia.org', 2, 0.85, TRUE),
('SRC_FC', 'FirstCycling', 'DATABASE', 'https://firstcycling.com', 3, 0.80, TRUE);

-- Example: Create Team Sky lineage and entities
INSERT INTO team_lineage (lineage_id, primary_name, founding_year) VALUES
('L_SKY_INEOS', 'Team Sky / Ineos Grenadiers', 2010);

INSERT INTO team_entity (entity_id, lineage_id, start_date, end_date) VALUES
('TE_SKY_2010', 'L_SKY_INEOS', '2010-01-01', '2018-12-31'),
('TE_INEOS_2019', 'L_SKY_INEOS', '2019-01-01', '2020-12-31'),
('TE_INEOS_GR_2021', 'L_SKY_INEOS', '2021-01-01', NULL);

-- Add properties
INSERT INTO team_property_link (property_id, entity_id, property_type, property_value, start_date, end_date, confidence_score) VALUES
('TPL_001', 'TE_SKY_2010', 'NAME', 'Team Sky', '2010-01-01', '2018-12-31', 1.0),
('TPL_002', 'TE_SKY_2010', 'UCI_CODE', 'SKY', '2012-01-01', '2018-12-31', 1.0),
('TPL_003', 'TE_SKY_2010', 'TIER', 'T1', '2010-01-01', '2018-12-31', 1.0),
('TPL_004', 'TE_SKY_2010', 'NATIONALITY', 'GB', '2010-01-01', '2018-12-31', 1.0);

-- Add sponsors
INSERT INTO sponsor_master (sponsor_id, legal_name, country, industry_sector) VALUES
('S_SKY', 'Sky Broadcasting', 'GB', 'Media/Broadcasting'),
('S_INEOS', 'INEOS Group', 'GB', 'Chemical Manufacturing');

INSERT INTO sponsor_brand_history (brand_id, sponsor_id, brand_name, start_date, is_primary) VALUES
('SB_SKY_001', 'S_SKY', 'Sky', '2010-01-01', TRUE),
('SB_INEOS_001', 'S_INEOS', 'Ineos', '2019-01-01', TRUE),
('SB_INEOS_002', 'S_INEOS', 'Ineos Grenadiers', '2021-01-01', TRUE);

-- Link sponsors to teams
INSERT INTO team_sponsor_link (link_id, entity_id, brand_id, sponsor_rank, display_order, start_date, end_date, confidence_score) VALUES
('TSL_001', 'TE_SKY_2010', 'SB_SKY_001', 'TITLE_PRIMARY', 1, '2010-01-01', '2018-12-31', 1.0),
('TSL_002', 'TE_INEOS_2019', 'SB_INEOS_001', 'TITLE_PRIMARY', 1, '2019-01-01', '2020-12-31', 1.0),
('TSL_003', 'TE_INEOS_GR_2021', 'SB_INEOS_002', 'TITLE_PRIMARY', 1, '2021-01-01', NULL, 1.0);

-- Add succession links
INSERT INTO team_succession_link (link_id, source_entity_id, target_entity_id, link_type, transition_date, confidence_score, source_references) VALUES
('SL_001', 'TE_SKY_2010', 'TE_INEOS_2019', 'DIRECT_CONTINUATION', '2019-01-01', 1.0, '["https://procyclingstats.com/team/team-sky", "https://en.wikipedia.org/wiki/Team_Sky"]'),
('SL_002', 'TE_INEOS_2019', 'TE_INEOS_GR_2021', 'DIRECT_CONTINUATION', '2021-01-01', 1.0, '["https://procyclingstats.com/team/ineos-grenadiers"]');
```

### 7.5 Performance Considerations

#### 7.5.1 Database Optimization
- **Indexes**: Create indexes on frequently queried fields (see CREATE INDEX statements above)
- **Denormalization**: Consider caching computed lineage paths for faster retrieval
- **Partitioning**: For very large datasets, partition tables by year
- **Query Optimization**: Use EXPLAIN ANALYZE to optimize slow queries
- **Connection Pooling**: Implement connection pooling for concurrent requests

#### 7.5.2 Frontend Optimization
- **Data Virtualization**: Only render visible portions of timeline
- **Progressive Loading**: Load data in chunks as user scrolls/zooms
- **Canvas vs SVG**: Consider HTML Canvas for rendering if >1000 teams visible
- **Debouncing**: Debounce zoom/pan events to reduce re-renders
- **Memoization**: Cache computed visual layouts
- **Lazy Loading**: Load detailed information only when requested (click/hover)
- **Service Workers**: Cache static assets and API responses

#### 7.5.3 API Optimization
- **Caching**: Implement HTTP caching headers (ETag, Cache-Control)
- **Compression**: Enable gzip/brotli compression
- **Pagination**: Always paginate large result sets
- **Field Selection**: Allow clients to request only needed fields
- **Query Optimization**: Use database query optimization techniques
- **Rate Limiting**: Implement rate limiting to prevent abuse

---

## 8. Implementation Phases

### 8.1 Phase 1: Foundation (Weeks 1-3)
**Goal**: Set up basic infrastructure and data model

**Tasks**:
1. Set up development environment
   - Install Python, Node.js, database
   - Create project structure
   - Initialize version control (Git)

2. Database setup
   - Create database schema
   - Implement migrations
   - Insert seed data (UCI tiers, data sources)

3. Basic backend API
   - Set up Flask/FastAPI project
   - Create basic CRUD endpoints for teams
   - Implement ORM models
   - Add API documentation

4. Basic frontend scaffold
   - Set up React/Vue project
   - Create basic layout and routing
   - Implement API client
   - Create simple data table view

**Deliverable**: Working CRUD application for teams (no visualization yet)

### 8.2 Phase 2: Data Scraping (Weeks 4-6)
**Goal**: Implement automated data collection

**Tasks**:
1. Scraper infrastructure
   - Set up scraping framework (Scrapy/Beautiful Soup)
   - Implement scheduling system
   - Create logging and error handling

2. Source-specific scrapers
   - ProCyclingStats scraper
   - Wikipedia scraper (multi-language)
   - FirstCycling scraper
   - Other sources as needed

3. Data processing pipeline
   - Data normalization functions
   - Conflict detection logic
   - Confidence score calculation
   - Database insertion/update logic

4. Scraper management interface
   - Dashboard for monitoring scrapes
   - Manual trigger capability
   - Configuration interface
   - Log viewer

**Deliverable**: Automated scraping system populating database

### 8.3 Phase 3: Core Visualization (Weeks 7-10)
**Goal**: Build the main timeline visualization

**Tasks**:
1. D3.js Sankey implementation
   - Create basic horizontal Sankey layout
   - Implement time-based X-axis
   - Create team bars with proper positioning
   - Draw connection lines between related teams

2. Color system
   - Implement sponsor-based coloring
   - Create horizontal gradients for transitions
   - Add vertical gradients for multi-color periods
   - Ensure accessibility (colorblind modes)

3. Zoom and pan
   - Implement zoom controls
   - Add pan functionality
   - Create time range selector/slider
   - Add fit-to-view functionality

4. Basic interactions
   - Hover effects and tooltips
   - Click to select team/lineage
   - Basic filtering (tier, date range)

**Deliverable**: Working interactive timeline visualization

### 8.4 Phase 4: Advanced Interactions (Weeks 11-13)
**Goal**: Implement sophisticated user interactions

**Tasks**:
1. Lineage highlighting
   - Click on team to highlight lineage
   - Visual glow effects
   - Connection line animation
   - Fade non-related teams

2. Sponsor tracking
   - Click sponsor to highlight all occurrences
   - Filter view to show only sponsor-related teams
   - Sponsor journey visualization

3. Sidebar information panel
   - Lineage timeline summary
   - Succession link details
   - Sponsor history
   - Team statistics

4. Search and advanced filtering
   - Global search functionality
   - Multi-criteria filters
   - Saved filter presets
   - URL-based state (shareable links)

**Deliverable**: Fully interactive visualization with all user features

### 8.5 Phase 5: Backend CMS (Weeks 14-17)
**Goal**: Build administrative interface for data management

**Tasks**:
1. CMS framework
   - Authentication system
   - Role-based access control
   - Dashboard layout
   - Navigation structure

2. Entity management interfaces
   - Team entity editor (with properties)
   - Lineage editor
   - Sponsor management
   - Succession link editor

3. Conflict resolution system
   - Conflict queue dashboard
   - Resolution interface
   - Automatic resolution rules
   - Conflict history tracking

4. Audit system
   - Audit log viewer
   - Change history for records
   - Version comparison
   - Rollback functionality

**Deliverable**: Complete CMS for data curation

### 8.6 Phase 6: Data Refinement (Weeks 18-20)
**Goal**: Populate and refine historical data

**Tasks**:
1. Historical data collection
   - Run full scrape of all sources
   - Process and normalize data
   - Review auto-detected conflicts

2. Manual data curation
   - Resolve ambiguous conflicts
   - Fill in gaps in data
   - Verify lineage connections
   - Add contextual notes

3. Sponsor database completion
   - Compile comprehensive sponsor list
   - Link sponsors to teams
   - Track brand name changes
   - Add color schemes

4. Quality assurance
   - Data validation checks
   - Consistency verification
   - Edge case testing
   - Community review (if applicable)

**Deliverable**: Comprehensive, curated dataset (1900-present)

### 8.7 Phase 7: Polish & Testing (Weeks 21-23)
**Goal**: Refine user experience and ensure stability

**Tasks**:
1. User experience refinement
   - Performance optimization
   - Loading state improvements
   - Error message polish
   - Animation tuning
   - Mobile responsiveness

2. Accessibility improvements
   - Keyboard navigation testing
   - Screen reader compatibility
   - Color contrast verification
   - Focus indicators
   - ARIA labels

3. Testing
   - Unit tests (backend logic)
   - Integration tests (API endpoints)
   - Frontend component tests
   - End-to-end tests (user workflows)
   - Performance testing
   - Cross-browser testing

4. Documentation
   - User guide/help documentation
   - API documentation
   - Developer setup guide
   - Data model documentation
   - Scraping guide

**Deliverable**: Production-ready application

### 8.8 Phase 8: Deployment & Launch (Week 24+)
**Goal**: Deploy to production and launch

**Tasks**:
1. Production setup
   - Set up production database
   - Configure production server
   - Set up SSL/HTTPS
   - Configure backups

2. Deployment
   - Deploy backend API
   - Deploy frontend application
   - Configure domain/hosting
   - Set up monitoring

3. Post-launch
   - Monitor for issues
   - Gather user feedback
   - Performance monitoring
   - Plan future enhancements

**Deliverable**: Live, publicly accessible website

---

## 9. Testing Strategy

### 9.1 Unit Testing

#### 9.1.1 Backend Unit Tests
**Test Coverage Areas**:
- Data normalization functions
- Conflict detection logic
- Confidence score calculation
- Date validation and parsing
- Lineage path calculation
- Query builders and filters

**Example Test Cases**:
```python
# test_data_normalization.py
def test_normalize_date_with_year_only():
    assert normalize_date("2010") == ("2010-01-01", 0.7)

def test_normalize_date_with_full_date():
    assert normalize_date("2010-06-15") == ("2010-06-15", 1.0)

def test_normalize_team_name():
    assert normalize_name("T-Mobile Team") == "T-Mobile"
    assert normalize_name("T - Mobile") == "T-Mobile"

# test_conflict_detection.py
def test_detect_date_conflict():
    values = [
        {"source": "PCS", "value": "2018-12-31"},
        {"source": "Wiki", "value": "2019-01-01"}
    ]
    assert detect_conflict(values) == True

def test_no_conflict_same_values():
    values = [
        {"source": "PCS", "value": "2018-12-31"},
        {"source": "Wiki", "value": "2018-12-31"}
    ]
    assert detect_conflict(values) == False

# test_confidence_scoring.py
def test_confidence_with_gold_standard():
    score = calculate_confidence([
        {"source": "PCS", "reliability": 1.0},
        {"source": "Wiki", "reliability": 0.85}
    ])
    assert score >= 0.95
```

**Testing Framework**: pytest (Python)

#### 9.1.2 Frontend Unit Tests
**Test Coverage Areas**:
- Utility functions (date formatting, color generation)
- Data transformation functions
- State management logic
- API client methods

**Example Test Cases**:
```javascript
// test/utils.test.js
describe('Date Utilities', () => {
  test('formats date range correctly', () => {
    expect(formatDateRange('2010-01-01', '2018-12-31'))
      .toBe('2010 - 2018');
  });
  
  test('handles current date', () => {
    expect(formatDateRange('2020-01-01', null))
      .toBe('2020 - Present');
  });
});

describe('Color Utilities', () => {
  test('generates gradient from sponsor colors', () => {
    const colors = generateGradient('#FF0000', '#0000FF', 5);
    expect(colors).toHaveLength(5);
    expect(colors[0]).toBe('#FF0000');
    expect(colors[4]).toBe('#0000FF');
  });
});
```

**Testing Framework**: Jest (JavaScript/React) or Vitest

### 9.2 Integration Testing

#### 9.2.1 API Endpoint Tests
**Test Coverage Areas**:
- CRUD operations for all entities
- Complex queries (lineage paths, sponsor journeys)
- Error handling (invalid data, authentication)
- Pagination and filtering
- Conflict resolution workflow

**Example Test Cases**:
```python
# test_api_integration.py
def test_create_team_entity(client, auth_token):
    response = client.post('/api/teams', 
        json={
            'entity_id': 'TE_TEST_001',
            'lineage_id': 'L_TEST',
            'start_date': '2020-01-01'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 201
    assert response.json['data']['entity_id'] == 'TE_TEST_001'

def test_get_lineage_timeline(client):
    response = client.get('/api/lineages/L_SKY_INEOS/timeline')
    assert response.status_code == 200
    data = response.json['data']
    assert len(data) > 0
    assert all('start_date' in item for item in data)

def test_resolve_conflict(client, auth_token):
    response = client.post('/api/conflicts/CNF_001/resolve',
        json={
            'resolved_value': '2018-12-31',
            'resolution_method': 'GOLD_STANDARD',
            'reason': 'Based on PCS data'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert response.json['data']['resolution_status'] == 'RESOLVED_MANUAL'
```

**Testing Framework**: pytest with Flask/FastAPI test client

#### 9.2.2 Database Integration Tests
**Test Coverage Areas**:
- Foreign key constraints
- Date range validations
- Cascade deletions
- Trigger functionality (updated_at)
- Complex joins and queries

### 9.3 End-to-End Testing

#### 9.3.1 User Workflow Tests
**Test Coverage Areas**:
- Complete user journeys from start to finish
- Browser-based interaction testing
- Visual regression testing

**Example Test Scenarios**:
```javascript
// e2e/timeline-navigation.spec.js
describe('Timeline Navigation', () => {
  test('User can zoom into specific time period', async () => {
    await page.goto('http://localhost:3000');
    await page.waitForSelector('.timeline-container');
    
    // Click zoom in button
    await page.click('.zoom-in-button');
    
    // Verify zoom level increased
    const zoomLevel = await page.evaluate(() => {
      return window.timeline.getZoomLevel();
    });
    expect(zoomLevel).toBeGreaterThan(1);
  });
  
  test('User can select and view lineage details', async () => {
    await page.goto('http://localhost:3000');
    
    // Click on a team bar
    await page.click('[data-team-id="TE_SKY_2010"]');
    
    // Verify sidebar opens
    await page.waitForSelector('.sidebar-panel');
    
    // Verify lineage is highlighted
    const highlightedTeams = await page.$('.team-bar.highlighted');
    expect(highlightedTeams.length).toBeGreaterThan(1);
    
    // Verify sidebar content
    const sidebarText = await page.$eval('.sidebar-panel', el => el.textContent);
    expect(sidebarText).toContain('Team Sky');
  });
});

// e2e/admin-workflow.spec.js
describe('Admin Data Management', () => {
  test('Admin can resolve a conflict', async () => {
    await page.goto('http://localhost:3000/admin/conflicts');
    await page.type('#username', 'admin');
    await page.type('#password', 'password');
    await page.click('#login-button');
    
    // Navigate to first conflict
    await page.click('.conflict-item:first-child .review-button');
    
    // Select resolution option
    await page.click('input[value="2018-12-31"]');
    
    // Add reason
    await page.type('#resolution-reason', 'Based on gold standard');
    
    // Submit resolution
    await page.click('#resolve-button');
    
    // Verify success message
    await page.waitForSelector('.success-message');
  });
});
```

**Testing Framework**: Playwright or Cypress

### 9.4 Performance Testing

#### 9.4.1 Load Testing
**Test Scenarios**:
- Concurrent users accessing timeline (10, 50, 100, 500 users)
- Database query performance under load
- API response times with large datasets
- Memory usage during extended sessions

**Tools**: Apache JMeter, k6, or Locust

**Performance Targets**:
- Page load time: < 2 seconds
- API response time (simple queries): < 100ms
- API response time (complex queries): < 500ms
- Visualization render time (10 years, 20 teams): < 1 second
- Memory usage: < 500MB for typical session

#### 9.4.2 Stress Testing
**Test Scenarios**:
- Maximum number of teams that can be displayed
- Database with 10,000+ team entities
- Continuous scrolling/zooming for extended periods
- Rapid filter changes

### 9.5 Browser Compatibility Testing

**Target Browsers**:
- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)

**Test Coverage**:
- All core visualization features
- All interactive elements
- Responsive design breakpoints
- Performance on different browsers

### 9.6 Accessibility Testing

**Testing Checklist**:
- [ ] Keyboard navigation works for all interactive elements
- [ ] Screen reader announces all content correctly
- [ ] Color contrast meets WCAG AA standards
- [ ] Focus indicators are visible
- [ ] Form validation errors are announced
- [ ] Alternative text for all images/icons
- [ ] Semantic HTML structure
- [ ] ARIA labels are appropriate
- [ ] Skip navigation links work
- [ ] Zoom to 200% doesn't break layout

**Tools**: 
- WAVE (Web Accessibility Evaluation Tool)
- axe DevTools
- Lighthouse (Chrome)
- Screen readers (NVDA, JAWS, VoiceOver)

---

## 10. Data Validation & Quality Assurance

### 10.1 Data Validation Rules

#### 10.1.1 Date Validation
**Rules**:
- Start date must be valid calendar date
- End date must be >= start date (if not NULL)
- Start date must be >= 1900-01-01
- End date must be <= current date (for defunct teams)
- No overlapping periods for same property type on same entity

**Implementation**:
- Database constraints (CHECK)
- API-level validation before insertion
- Frontend form validation

#### 10.1.2 Relationship Validation
**Rules**:
- Entity must belong to exactly one lineage
- Succession links cannot create cycles
- Target entity must exist before source entity ends
- No self-referencing succession links

**Implementation**:
- Database foreign key constraints
- Graph traversal algorithm to detect cycles
- API validation logic

#### 10.1.3 Data Completeness Checks
**Required Fields**:
- Every Team_Entity must have:
  - At least one NAME property
  - At least one TIER property
  - At least one NATIONALITY property
- Every Sponsor_Master must have:
  - Legal name
  - At least one brand name

**Quality Metrics**:
- Percentage of teams with complete data
- Percentage of teams with verified succession links
- Average confidence score across database
- Number of unresolved conflicts

### 10.2 Data Quality Dashboard

Display metrics in admin dashboard:
```
┌─ Data Quality Overview ─────────────────────┐
│                                             │
│ Total Teams: 1,234                          │
│ Complete Records: 89% ✓                     │
│ Missing Data: 11% ⚠                         │
│                                             │
│ Average Confidence: 0.87                    │
│ Unresolved Conflicts: 23                    │
│                                             │
│ By Decade:                                  │
│ 1900-1950: 45% complete ⚠                   │
│ 1950-2000: 78% complete ⚠                   │
│ 2000-2025: 95% complete ✓                   │
│                                             │
│ [View Detailed Report]                      │
└───────────────────────────────────────────────┘
```

### 10.3 Automated Data Quality Checks

**Scheduled Jobs**:
- Daily: Check for orphaned records
- Daily: Validate all date ranges
- Weekly: Verify lineage path integrity
- Weekly: Check for duplicate entities
- Monthly: Comprehensive data quality report

**Alerts**:
- Email notification for critical issues
- Dashboard warnings for minor issues
- Slack/Discord integration (optional)

---

## 11. Deployment & Operations

### 11.1 Local Development Setup

#### 11.1.1 Prerequisites
```bash
# Required software
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+ (or SQLite for simple setup)
- Git
```

#### 11.1.2 Setup Instructions
```bash
# Clone repository
git clone https://github.com/yourusername/cycling-timeline.git
cd cycling-timeline

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database setup
createdb cycling_timeline  # For PostgreSQL
python manage.py migrate   # Run migrations
python manage.py seed      # Load seed data

# Start backend server
python manage.py runserver

# Frontend setup (new terminal)
cd ../frontend
npm install
npm run dev

# Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:5000
# API Docs: http://localhost:5000/docs
```

#### 11.1.3 Environment Configuration
```bash
# .env file (backend)
DATABASE_URL=postgresql://user:pass@localhost/cycling_timeline
SECRET_KEY=your-secret-key-here
DEBUG=True
CORS_ORIGINS=http://localhost:5173

# .env file (frontend)
VITE_API_BASE_URL=http://localhost:5000/api
```

### 11.2 Production Deployment

#### 11.2.1 Server Requirements
**Minimum Specifications**:
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB SSD
- OS: Ubuntu 22.04 LTS (or similar Linux)

**Recommended Specifications** (for moderate traffic):
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD

#### 11.2.2 Deployment Steps

**1. Prepare Server**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.9 python3-pip nginx postgresql git supervisor

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs
```

**2. Deploy Backend**
```bash
# Create application user
sudo useradd -m -s /bin/bash cyclingapp

# Clone repository
sudo -u cyclingapp git clone https://github.com/yourusername/cycling-timeline.git /home/cyclingapp/app

# Set up Python environment
cd /home/cyclingapp/app/backend
sudo -u cyclingapp python3 -m venv venv
sudo -u cyclingapp venv/bin/pip install -r requirements.txt

# Set up database
sudo -u postgres createdb cycling_timeline
sudo -u postgres createuser cyclingapp
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cycling_timeline TO cyclingapp;"

# Run migrations
sudo -u cyclingapp venv/bin/python manage.py migrate

# Configure Gunicorn
sudo -u cyclingapp venv/bin/pip install gunicorn

# Create Gunicorn service
sudo nano /etc/supervisor/conf.d/cycling-api.conf
```

**Supervisor Configuration**:
```ini
[program:cycling-api]
command=/home/cyclingapp/app/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
directory=/home/cyclingapp/app/backend
user=cyclingapp
autostart=true
autorestart=true
stderr_logfile=/var/log/cycling-api.err.log
stdout_logfile=/var/log/cycling-api.out.log
```

**3. Deploy Frontend**
```bash
# Build frontend
cd /home/cyclingapp/app/frontend
sudo -u cyclingapp npm install
sudo -u cyclingapp npm run build

# Output will be in /home/cyclingapp/app/frontend/dist
```

**4. Configure Nginx**
```nginx
# /etc/nginx/sites-available/cycling-timeline
server {
    listen 80;
    server_name yourdomain.com;
    
    # Frontend
    location / {
        root /home/cyclingapp/app/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static {
        alias /home/cyclingapp/app/backend/static;
        expires 30d;
    }
}
```

**Enable site and restart Nginx**:
```bash
sudo ln -s /etc/nginx/sites-available/cycling-timeline /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**5. SSL/HTTPS Setup**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com
```

#### 11.2.3 Database Backups
```bash
# Create backup script
sudo nano /usr/local/bin/backup-cycling-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/backups/cycling-timeline"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U cyclingapp cycling_timeline | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-cycling-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-cycling-db.sh
```

### 11.3 Monitoring & Logging

#### 11.3.1 Application Monitoring
**Tools**:
- **Server monitoring**: Netdata or Prometheus + Grafana
- **Application errors**: Sentry
- **Uptime monitoring**: UptimeRobot or Pingdom

**Key Metrics to Monitor**:
- Server CPU, RAM, disk usage
- Database connections and query performance
- API response times
- Error rates
- Active users
- Scraper job success/failure rates

#### 11.3.2 Log Management
**Log Locations**:
- Application logs: `/var/log/cycling-api.out.log`
- Error logs: `/var/log/cycling-api.err.log`
- Nginx access: `/var/log/nginx/access.log`
- Nginx errors: `/var/log/nginx/error.log`

**Log Rotation**:
```bash
# /etc/logrotate.d/cycling-timeline
/var/log/cycling-api.*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 cyclingapp cyclingapp
    sharedscripts
}
```

### 11.4 Scaling Considerations (Future)

#### 11.4.1 Horizontal Scaling
- Load balancer (Nginx, HAProxy) in front of multiple API servers
- Read replicas for database
- Redis for caching frequent queries
- CDN for frontend static assets

#### 11.4.2 Performance Optimization
- Database query optimization
- API response caching
- Frontend code splitting
- Lazy loading of images/data
- Service workers for offline capability

---

## 12. Future Enhancements

### 12.1 Phase 1 Enhancements (After Initial Launch)

1. **Advanced Search**
   - Full-text search across all text fields
   - Search by rider name (requires rider data collection)
   - Search by race wins/achievements

2. **Export Functionality**
   - Export filtered timeline as image (PNG/SVG)
   - Export data as CSV/JSON
   - Generate PDF reports for specific lineages

3. **User Accounts**
   - User registration and authentication
   - Save favorite teams/lineages
   - Custom color schemes/themes
   - Annotation system (user notes on teams)

4. **Enhanced Visualizations**
   - Alternative view modes (list, grid, graph)
   - Mini-map for navigation
   - Animated timeline playback (watch history unfold year by year)
   - Heat map view (activity by region/country)

### 12.2 Phase 2 Enhancements (Long-term)

1. **Extended Data**
   - Rider rosters and transfers
   - Race results and victories
   - Team budgets (if available)
   - Equipment/bike sponsors history
   - Team manager history

2. **Social Features**
   - Public API for third-party integrations
   - Embedded widget for other websites
   - Share specific views on social media
   - Community contributions/suggestions

3. **Mobile App**
   - Native iOS/Android app
   - Touch-optimized visualization
   - Offline mode with cached data

4. **Analytics & Insights**
   - Statistical analysis (most successful sponsors, longest lineages)
   - Prediction models (team stability, sponsor loyalty)
   - Trend analysis (sponsorship patterns over time)
   - Network analysis (which teams are most connected)

5. **Internationalization**
   - Multi-language interface
   - Translated team names where applicable
   - Region-specific views

6. **API & Integrations**
   - Public REST API for external developers
   - Webhook notifications for data updates
   - Integration with Strava, TrainingPeaks
   - Integration with cycling news sites

---

## 13. Documentation Requirements

### 13.1 User Documentation

#### 13.1.1 User Guide
**Content**:
- Getting started / welcome tour
- How to navigate the timeline
- Understanding the visualization
- Using filters and search
- Reading lineage connections
- Interpreting sponsor colors
- Keyboard shortcuts reference

**Format**: Interactive help overlay + separate documentation page

#### 13.1.2 FAQ
**Topics**:
- What data sources are used?
- How accurate is the data?
- What does "lineage" mean?
- Why does team X show as connected to team Y?
- How can I suggest corrections?
- How often is data updated?

### 13.2 Developer Documentation

#### 13.2.1 Setup Guide
- Prerequisites and installation
- Environment configuration
- Running locally
- Database setup and seeding
- Testing procedures

#### 13.2.2 Architecture Documentation
- System overview diagram
- Data model documentation
- API endpoint reference (OpenAPI/Swagger)
- Frontend component library
- State management guide

#### 13.2.3 Contributing Guide
- Code style guidelines
- Git workflow
- Pull request process
- Testing requirements
- Documentation standards

### 13.3 Data Model Documentation

#### 13.3.1 Entity Relationship Diagrams
- Visual ER diagram showing all tables
- Relationship cardinality
- Key constraints

#### 13.3.2 Data Dictionary
- Complete list of all tables and fields
- Field descriptions and constraints
- Example data for each table
- Enum value definitions

### 13.4 Operations Documentation

#### 13.4.1 Deployment Guide
- Server requirements
- Step-by-step deployment instructions
- Configuration management
- SSL certificate setup
- Backup procedures

#### 13.4.2 Maintenance Guide
- Regular maintenance tasks
- Database optimization
- Log management
- Updating the application
- Troubleshooting common issues

---

## 14. Risk Assessment & Mitigation

### 14.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data scraping blocked by source sites | Medium | High | Implement polite scraping with delays; respect robots.txt; have manual data entry fallback |
| Database performance degrades with scale | Medium | High | Implement proper indexing; use query optimization; plan for caching layer |
| Browser compatibility issues | Low | Medium | Test on all major browsers; use progressive enhancement; provide fallbacks |
| Data conflicts cannot be auto-resolved | High | Medium | Robust manual resolution interface; clear documentation of edge cases |

### 14.2 Data Quality Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Inaccurate historical data | High | High | Multiple source verification; confidence scoring; community review system |
| Missing data for early years (pre-1980) | High | Medium | Accept incompleteness; clearly mark confidence levels; allow manual additions |
| Conflicting information across sources | High | Medium | Conflict resolution system; source prioritization; transparent audit trail |
| Lineage relationships disputed | Medium | Medium | Allow multiple interpretations; link qualifiers; community input |

### 14.3 Project Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep | Medium | High | Clear phase definitions; strict MVP scope; prioritized backlog |
| Development time underestimated | Medium | Medium | Add buffer time; incremental delivery; flexible timeline |
| Hosting costs exceed budget | Low | Medium | Start with minimal hosting; optimize before scaling; monitor costs |
| Limited user adoption | Medium | Low | Market to cycling communities; provide value quickly; gather feedback |

---

## 15. Success Metrics

### 15.1 Technical Metrics
- **Uptime**: 99.5% or higher
- **Page Load Time**: < 2 seconds (on typical connection)
- **API Response Time**: < 100ms for simple queries
- **Error Rate**: < 0.1% of requests
- **Test Coverage**: > 80% for critical paths

### 15.2 Data Quality Metrics
- **Data Completeness**: > 90% for period 2000-present
- **Confidence Score Average**: > 0.85
- **Unresolved Conflicts**: < 5% of total records
- **Data Freshness**: Updated within 7 days of real-world changes

### 15.3 User Engagement Metrics (Post-Launch)
- **Active Users**: Target based on niche audience
- **Session Duration**: > 5 minutes average
- **Return Visitor Rate**: > 30%
- **Feature Usage**: > 50% of users interact with filters/search

---

## 16. Conclusion

This specification provides a comprehensive blueprint for developing the Professional Cycling Team Timeline Visualization platform. The system is designed to handle the complex, temporal, and networked nature of professional cycling team history while remaining maintainable and extensible.

### 16.1 Key Success Factors

1. **Flexible Data Model**: The normalized, time-bound property system allows for accurate representation of cycling's complex history
2. **Multi-Source Data Strategy**: Combining automated scraping with manual curation ensures comprehensive and accurate data
3. **Intuitive Visualization**: The Sankey-style timeline provides an engaging way to understand team lineages and sponsor movements
4. **Robust Conflict Resolution**: The conflict detection and resolution system handles the inherent ambiguity in historical cycling data
5. **Comprehensive Audit Trail**: Every change is logged, allowing for transparency and accountability

### 16.2 Development Philosophy

- **Start Simple**: Begin with core functionality (phases 1-4) before adding advanced features
- **Iterate Based on Data**: Let real data shape the system's evolution
- **Embrace Ambiguity**: The system acknowledges uncertainty rather than forcing false precision
- **Community-Driven**: Design for eventual community contributions and corrections
- **Performance Matters**: Optimize for smooth interactions even with 125 years of data

### 16.3 Next Steps

1. Review and approve this specification
2. Set up development environment
3. Begin Phase 1 implementation
4. Establish regular check-ins to review progress
5. Iterate based on learnings and feedback

---

## Appendix A: Glossary

**Team Entity**: A specific configuration of a team during a defined time period (name, sponsor, ownership combination)

**Team Lineage**: The continuous "spiritual" entity representing a team through all its transformations

**Succession Link**: A relationship between two team entities showing how one led to another

**Confidence Score**: A numeric value (0.0-1.0) indicating the reliability of a data point

**Tier**: The competitive level of a team (T1=WorldTour, T2=ProTeam, etc.)

**Gold Standard**: The most reliable data source (ProCyclingStats for this project)

**Conflict**: Disagreement between different data sources about the same fact

**Property Link**: A time-bound attribute associated with a team entity

---

## Appendix B: Example Data Scenarios

### Scenario 1: Simple Name Change (Team Sky → Ineos)
```
Team Entity 1:
- ID: TE_SKY_2010
- Lineage: L_SKY_INEOS
- Start: 2010-01-01
- End: 2018-12-31
- Properties: NAME="Team Sky", UCI_CODE="SKY", TIER="T1"
- Sponsor: Sky (TITLE_PRIMARY)

Succession Link:
- Type: DIRECT_CONTINUATION
- Date: 2019-01-01

Team Entity 2:
- ID: TE_INEOS_2019
- Lineage: L_SKY_INEOS (same lineage)
- Start: 2019-01-01
- End: 2020-12-31
- Properties: NAME="Team Ineos", UCI_CODE="INS", TIER="T1"
- Sponsor: Ineos (TITLE_PRIMARY)
```

### Scenario 2: Team Split (TI-Raleigh → Kwantum + Panasonic)
```
Source Entity:
- ID: TE_RALEIGH_1972
- Lineage: L_RALEIGH
- Start: 1972-01-01
- End: 1983-12-31

Succession Link 1:
- Source: TE_RALEIGH_1972
- Target: TE_KWANTUM_1984
- Type: SPLIT_EQUAL
- Staff Transfer: 50%
- Date: 1983-12

Target Entity 1:
- ID: TE_KWANTUM_1984
- Lineage: L_KWANTUM (new lineage)
- Start: 1984-01-01

Succession Link 2:
- Source: TE_RALEIGH_1972
- Target: TE_PANASONIC_1984
- Type: SPLIT_EQUAL
- Staff Transfer: 50%
- Date: 1983-12

Target Entity 2:
- ID: TE_PANASONIC_1984
- Lineage: L_PANASONIC (new lineage)
- Start: 1984-01-01
```

### Scenario 3: Sponsor Movement (Soudal: Lotto → QuickStep)
```
Sponsor Master:
- ID: S_SOUDAL
- Legal Name: Soudal Holding
- Country: BE

Sponsor Brand:
- ID: SB_SOUDAL
- Sponsor: S_SOUDAL
- Brand Name: Soudal
- Start: 1990-01-01 (no end date)

Team-Sponsor Link 1:
- Team Entity: TE_LOTTO_2021
- Brand: SB_SOUDAL
- Rank: TITLE_PRIMARY
- Start: 2021-01-01
- End: 2024-12-31

Team-Sponsor Link 2:
- Team Entity: TE_QUICKSTEP_2025
- Brand: SB_SOUDAL
- Rank: TITLE_SECONDARY
- Start: 2025-01-01
- End: NULL (current)
```

---

## Appendix C: Technology Stack Summary

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Frontend Framework** | React or Vue.js | Modern, component-based, excellent for complex UIs |
| **Visualization** | D3.js | Industry standard for data visualization, flexible |
| **Backend Framework** | Flask or FastAPI | Python-based, simple, well-documented |
| **Database** | PostgreSQL | Robust relational DB, excellent for temporal data |
| **ORM** | SQLAlchemy | Powerful, flexible, works well with Flask/FastAPI |
| **Scraping** | Beautiful Soup + Requests | Simple, effective for HTML parsing |
| **Scheduling** | APScheduler | Easy Python-based task scheduling |
| **Testing (Backend)** | pytest | De facto standard for Python testing |
| **Testing (Frontend)** | Jest/Vitest | Fast, comprehensive JavaScript testing |
| **E2E Testing** | Playwright/Cypress | Modern, reliable browser automation |
| **Deployment** | Nginx + Gunicorn | Production-ready, battle-tested |
| **Hosting** | VPS or PaaS | Flexible, scalable as needed |

---

**Document Version**: 1.0  
**Last Updated**: 2024-11-14  
**Author**: Specification compiled from collaborative interview process  
**Status**: Ready for Development 