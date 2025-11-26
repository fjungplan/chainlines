# **Cycling Team Lineage Timeline – Master Technical Specification**

Version: 1.0  
Status: Ready for Implementation  
Architecture Style: Managerial Continuity / Event-Driven Wiki

## **1\. Executive Summary**

Product: An open-source, public wiki visualizing the evolutionary history of professional cycling teams (1900–Present).  
Core Concept: The system tracks the "Managerial Node" (the legal/license holder) through time. Users do not edit the graph directly; they trigger "Events" (Merges, Splits, Rebrands) via a wizard.  
Visual Signature: A horizontal "River" (Sankey) diagram where team bars are "Jersey Slices"—stacked vertical ribbons representing the sponsor mix of that era.  
Data Strategy: Automated scrapers "seed" the data using a polite, low-velocity strategy. Manual edits by users lock the data against future scraper overwrites.

## **2\. Domain Glossary (Crucial Definitions)**

* **Managerial Node:** The persistent entity (e.g., "Soudal Quick-Step's management company"). It survives name changes. It only ends upon dissolution or total license sale.  
* **Team Era:** A specific season (Year) within a Node. Contains the specific metadata for that year (e.g., "2012 Team Sky").  
* **Jersey Slice:** The visual representation of a Team Era. A vertical bar split by color (e.g., 60% Blue, 40% White) based on sponsor prominence.  
* **Spiritual Succession:** A lineage link where a team dies legally, but staff/riders move to a new entity. Represented visually by dashed lines.  
* **The Gentle Scraper:** An infrastructure pattern where the scraper runs slowly (high latency) without proxies to avoid IP bans.

## **3\. User Experience (UX) Requirements**

### **3.1 Desktop Visualization ("The River")**

* **Library:** D3.js.  
* **Layout Algorithm:** **Optimized Topology**.  
  * The Y-axis positioning MUST prioritize straight lines and minimize link crossings.  
  * *Constraint:* Do NOT enforce strict "Tier Bands" (WorldTour at top) if it causes visual spaghetti.  
* **LOD (Level of Detail) System:**  
  * *Zoom Level 0 (Overview):* Unified, smooth Bézier curves for all connections.  
  * *Zoom Level 1 (Deep Zoom):* Reveal connection types (Solid \= Legal Transfer, Dashed \= Spiritual).  
* **Team Node Rendering:**  
  * Nodes must render as "Jersey Slices" based on team\_sponsor\_link.prominence.

### **3.2 Mobile Visualization ("The Companion")**

* **Breakpoint:** \< 768px width.  
* **Behavior:** The D3 Graph is **disabled**.  
* **View:** **Vertical List View**.  
* **Interaction:** Search-based. User types "Visma", selects result, sees a vertical chronological timeline (Year | Name | Status).

### **3.3 The "Wizard" Editor**

* **Constraint:** Users cannot edit the Graph Topology manually.  
* **Workflow:** User selects a Team $\\rightarrow$ Clicks "Edit" $\\rightarrow$ Selects Action:  
  1. **Correct Info:** Edit metadata (Name, Tier) for a specific year.  
  2. **Structural Event:** Trigger a wizard for "Merge," "Split," or "Dissolve."  
     * *Logic:* The system backend handles the closing of the old Node and creation of new Node(s) and Link(s).

### **3.4 Moderation & Auth**

* **Provider:** Google OAuth (OIDC).  
* **User Tiers:**  
  1. **Guest:** Read-only.  
  2. **New User:** Edits go to **Pre-moderation Queue**.  
  3. **Trusted User:** Auto-promoted after $N$ (config: 5\) approved edits. **Post-moderation** (Changes live instantly).  
  4. **Admin:** Ban users, Revert revisions, Force Scraper.

## **4\. System Architecture**

### **4.1 Tech Stack**

* **Frontend:** React (UI Shell) \+ D3.js (Visualization Canvas).  
* **Backend:** Python **FastAPI** (Async support required for scraping/concurrency).  
* **Database:** **PostgreSQL** (Relational integrity is mandatory).  
* **Auth:** Firebase Auth or Direct Google OIDC.  
* **Containerization:** Docker Compose.

### **4.2 Infrastructure: "The Gentle Scraper"**

* **Host:** Single VPS (Self-Hosted).  
* **Proxy Strategy:** **None** (Use host IP).  
* **Scheduling Strategy:** **Round-Robin High-Latency**.  
  * The scheduler cycles targets: PCS \-\> Wikipedia \-\> FirstCycling \-\> Sleep.  
  * **Delay:** MUST wait 15–30 seconds between requests to the *same domain*.

## **5\. Data Model (PostgreSQL Schema)**

### **5.1 Core Lineage**

\-- The persistent legal entity  
CREATE TABLE team\_node (  
    node\_id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    founding\_year INT,  
    dissolution\_year INT NULL,  
    created\_at TIMESTAMP DEFAULT NOW(),  
    updated\_at TIMESTAMP  
);

\-- Yearly snapshots (The "Era")  
CREATE TABLE team\_era (  
    era\_id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    node\_id UUID REFERENCES team\_node(node\_id),  
    season\_year INT NOT NULL,  
    registered\_name VARCHAR NOT NULL, \-- e.g. "RadioShack-Nissan"  
    uci\_code VARCHAR(3),  
    tier\_level INT, \-- 1=WT, 2=Pro, 3=Conti  
      
    \-- Scraper Logic  
    source\_origin VARCHAR, \-- 'scraper\_pcs' or 'user\_google\_123'  
    is\_manual\_override BOOLEAN DEFAULT FALSE, \-- If TRUE, Scraper ignores this row  
      
    UNIQUE(node\_id, season\_year)  
);

### **5.2 Lineage Graph Links**

CREATE TABLE lineage\_event (  
    event\_id UUID PRIMARY KEY,  
    previous\_node\_id UUID REFERENCES team\_node(node\_id),  
    next\_node\_id UUID REFERENCES team\_node(node\_id),  
    event\_year INT,  
    event\_type VARCHAR, \-- 'LEGAL\_TRANSFER', 'SPIRITUAL\_SUCCESSION', 'MERGE', 'SPLIT'  
    notes TEXT  
);

### **5.3 Sponsor Hierarchy (High Fidelity)**

\-- Parent Corp (e.g. "Soudal Group")  
CREATE TABLE sponsor\_master (  
    master\_id UUID PRIMARY KEY,  
    legal\_name VARCHAR,  
    industry\_sector VARCHAR  
);

\-- Marketing Brand (e.g. "Lotto-Soudal", "Soudal Quick-Step")  
CREATE TABLE sponsor\_brand (  
    brand\_id UUID PRIMARY KEY,  
    master\_id UUID REFERENCES sponsor\_master(master\_id),  
    brand\_name VARCHAR,  
    default\_hex\_color VARCHAR(7) \-- \#FF0000  
);

\-- The "Jersey Slice" Logic  
CREATE TABLE team\_sponsor\_link (  
    link\_id UUID PRIMARY KEY,  
    era\_id UUID REFERENCES team\_era(era\_id),  
    brand\_id UUID REFERENCES sponsor\_brand(brand\_id),  
    rank\_order INT, \-- 1 \= Title, 2 \= Secondary  
    prominence\_percent INT CHECK (prominence\_percent \<= 100\) \-- Determines bar height  
);

## **6\. Logic & Algorithms**

### **6.1 Scraper "Seeder" Logic**

1. **Check:** Does team\_era exist for Team X in Year Y?  
2. **If No:** Create it.  
3. **If Yes:** Check is\_manual\_override.  
   * If TRUE: **Abort**. Do not touch.  
   * If FALSE: Update fields if data differs.

### **6.2 D3 Visualization Logic**

* **Data Fetch:** API returns a JSON graph of { nodes: \[\], links: \[\] }.  
* **Topology Calculation:** Use d3-sankey or d3-dag.  
  * *Sorting:* Sort Y-Coordinates to minimize link.source.y \- link.target.y delta.  
* **Gradient Generation:**  
  * For every Node, generate an SVG \<linearGradient\> definition based on the team\_sponsor\_link colors and percentages.

## **7\. API Definition (Key Endpoints)**

### **7.1 Public Read**

* GET /api/v1/timeline?start\_year=1990\&end\_year=2024  
  * Returns structured Graph JSON (Nodes \+ Links) optimized for D3.  
* GET /api/v1/team/{node\_id}  
  * Returns full history list for Mobile View.

### **7.2 Wizard/Write (Protected)**

* POST /api/v1/wizard/event  
  * Payload: { type: "MERGE", source\_nodes: \[id\_a, id\_b\], year: 2012, new\_name: "..." }  
  * *Backend Logic:* Closes id\_a and id\_b in DB. Creates new node\_c. Creates lineage\_event links.

### **7.3 Scraper Control (Admin)**

* POST /api/v1/admin/scraper/trigger  
  * Payload: { target: "PCS", team\_id: "...", force: boolean }

## **8\. Testing Strategy**

### **8.1 Backend (Pytest)**

* **Graph Integrity:** Test that a "Split" event results in 1 closed node and 2 active nodes.  
* **Sponsor Constraints:** Ensure sum(prominence\_percent) for an era never exceeds 100\.

### **8.2 Scraper Integration**

* **Locking:** Create a record with manual\_override=True. Run scraper mock. Assert record is unchanged.  
* **Rate Limit:** Mock the generic HTTP client. Assert sleep(15) is called between requests.

### **8.3 Frontend (Cypress/Playwright)**

* **Responsive Switch:** Test that resizing the viewport \< 768px hides \#d3-container and shows \#list-view-container.  
* **Wizard Flow:** Simulate a user logging in, clicking "Edit," and submitting a form.

## **9\. Implementation Roadmap**

1. **Phase 0: Skeleton**  
   * Setup Docker Compose (Postgres \+ FastAPI).  
   * Define SQLAlchemy Models.  
2. **Phase 1: The Data Core**  
   * Implement CRUD for Nodes/Eras.  
   * Setup Google Auth & User Roles.  
3. **Phase 2: The Gentle Scraper**  
   * Build the Round-Robin Scheduler.  
   * Implement PCS Parser.  
   * Seed the DB with major teams.  
4. **Phase 3: The Companion (Mobile)**  
   * Build React List View.  
   * *Milestone:* Usable "Wikipedia-style" list on mobile.  
5. **Phase 4: The River (Desktop)**  
   * Implement D3.js logic.  
   * Implement "Jersey Slice" SVG generation.  
6. **Phase 5: The Wizard**  
   * Build the "Structural Event" UI forms.  
   * Enable Moderation Queue.