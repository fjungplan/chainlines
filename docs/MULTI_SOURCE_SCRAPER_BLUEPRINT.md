# Multi-Source Scraper Implementation Blueprint

**Version**: 1.0  
**Date**: 2026-01-06  
**Reference**: [MULTI_SOURCE_SCRAPER_SPECIFICATION.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/MULTI_SOURCE_SCRAPER_SPECIFICATION.md)

## Overview

This blueprint breaks down the Multi-Source Scraper into implementable chunks. Each chunk builds on the previous, ensuring no orphaned code and continuous integration.

### TDD Principle (MANDATORY)
Every chunk follows this strict order:
1. **Tests First** - Write failing tests before any implementation
2. **Implementation** - Write minimum code to pass tests
3. **Verification** - Run `pytest` to confirm all tests pass
4. **Commit** - Atomic commit with descriptive message

---

## Phase A: Infrastructure Foundation

### A1. File-Based Caching System
**Goal**: Enable resume capability by caching HTTP responses and LLM results.

**Steps**:
1. Create `CacheManager` class with `get()` and `set()` methods
2. Implement URL hashing for cache keys
3. Integrate into `BaseScraper.fetch()` method
4. Add `force_refresh` parameter

**Dependencies**: None  
**Tests**: Unit tests for cache hit/miss scenarios

---

### A2. FirstCycling Grand Tour Index
**Goal**: Build the "Bouncer" relevance filter for pre-1991 teams.

**Steps**:
1. Create `FirstCyclingScraper` with 10s rate limit
2. Implement GT start list parser (extract team names)
3. Create `GTRelevanceIndex` class to manage cached JSON
4. Implement `is_relevant(team_name, year)` method

**Dependencies**: A1 (CacheManager)  
**Tests**: Parser tests with sample HTML, relevance check tests

---

### A3. Phase 1 Discovery Refactor
**Goal**: Implement Dual Seeding + Graph Traversal + Relevance Filtering.

**Steps**:
1. Update `DiscoveryService` to accept year range (1900-2026)
2. Implement Dual Seeding (Modern + Historical)
3. Integrate `GTRelevanceIndex` as filter
4. Add tier-based filtering logic per era

**Dependencies**: A2 (GTRelevanceIndex)  
**Tests**: Integration tests for filtering behavior

---

## Phase B: Entity Resolution (The Rosetta Stone)

### B1. Wikidata Resolver Service
**Goal**: Map team names to Wikidata entities and extract sitelinks.

**Steps**:
1. Create `WikidataResolver` class
2. Implement SPARQL query for cycling teams
3. Parse response to extract Q-ID, sitelinks, aliases
4. Implement fallback for no-match scenarios

**Dependencies**: A1 (CacheManager for SPARQL caching)  
**Tests**: Unit tests with mocked SPARQL responses

---

### B2. Data Model Updates
**Goal**: Add external_ids and wikipedia_history_content fields.

**Steps**:
1. Add `external_ids` JSONB column to `TeamNode`
2. Add `wikipedia_history_content` TEXT column to `TeamEra`
3. Create Alembic migration
4. Update Pydantic schemas

**Dependencies**: None (can be parallel with B1)  
**Tests**: Migration verification

---

## Phase C: Parallel Workers & Fan-Out

### C1. Worker Infrastructure
**Goal**: Create a unified worker pattern for source scraping.

**Steps**:
1. Create abstract `SourceWorker` base class
2. Implement `WikipediaWorker` (fetch + extract History section)
3. Implement `CyclingRankingWorker` (fetch + parse dates)
4. Implement `MemoireWorker` (Wayback + parse)

**Dependencies**: A1 (CacheManager), B1 (WikidataResolver for URLs)  
**Tests**: Unit tests for each parser

---

### C2. Phase 2 Enrichment Orchestration
**Goal**: Wire workers into Phase 2 for parallel enrichment.

**Steps**:
1. Update `AssemblyOrchestrator` to call WikidataResolver
2. Fan-out to workers in parallel (asyncio.gather)
3. Collect results into unified `EnrichedTeamData` object
4. Pass to existing sponsor extraction logic

**Dependencies**: C1 (Workers), B1 (WikidataResolver)  
**Tests**: Integration tests with mocked workers

---

## Phase D: Conflict Arbitration

### D1. Conflict Arbiter Service
**Goal**: Use Deepseek Reasoner to decide Split vs Merge.

**Steps**:
1. Create `ConflictArbiter` class
2. Design arbitration prompt with Legal Supremacy rules
3. Implement structured output parsing (ArbitrationResult)
4. Add confidence threshold logic (90%+)

**Dependencies**: LLMService (existing)  
**Tests**: Unit tests with mocked LLM responses

---

### D2. Phase 2 Arbiter Integration
**Goal**: Invoke arbiter when sources conflict.

**Steps**:
1. Detect conflicts (date mismatch, name mismatch)
2. Call `ConflictArbiter.decide()` with evidence
3. Create PENDING edit if confidence < 90%
4. Auto-apply if confidence >= 90%

**Dependencies**: D1 (ConflictArbiter), C2 (Enrichment)  
**Tests**: End-to-end tests for conflict scenarios

---

## Phase E: Lineage Enhancement

### E1. Phase 3 Wikipedia Context
**Goal**: Feed Wikipedia History text to lineage decisions.

**Steps**:
1. Retrieve stored `wikipedia_history_content` from TeamEra
2. Update `DECIDE_LINEAGE_PROMPT` to include history text
3. Enhance `OrphanDetector` with context-aware matching

**Dependencies**: B2 (Data Model), Phase 2 must store history  
**Tests**: Unit tests for prompt formatting

---

## Phase F: Monitoring & UI

### F1. SSE Event Stream
**Goal**: Provide real-time structured logging to Admin UI.

**Steps**:
1. Create `SSEManager` utility class
2. Implement `GET /api/admin/scraper/runs/{run_id}/stream` endpoint
3. Emit `log`, `progress`, `decision` events
4. Update Phase 2/3 to emit events

**Dependencies**: Existing API infrastructure  
**Tests**: API endpoint tests

---

## Dependency Graph

```
A1 ─┬─> A2 ──> A3
    │
    └─> B1 ──> C1 ──> C2 ──> D2 ──> E1
              │
B2 ──────────>┘
              
D1 ──────────────────> D2

F1 (independent, can be parallel)
```

---

## Chunk Sizing Review

| Chunk | Estimated Tool Calls | Risk Level |
|-------|---------------------|------------|
| A1    | 5-8                 | Low        |
| A2    | 8-12                | Medium     |
| A3    | 6-10                | Medium     |
| B1    | 6-10                | Low        |
| B2    | 3-5                 | Low        |
| C1    | 10-15               | Medium     |
| C2    | 8-12                | Medium     |
| D1    | 5-8                 | Medium     |
| D2    | 6-10                | High       |
| E1    | 4-6                 | Low        |
| F1    | 6-10                | Low        |

**Total**: ~70-100 tool calls

---

## Sub-Chunk Breakdown (Right-Sizing)

### A1: File-Based Caching System
- **A1.1**: Create `cache.py` with `CacheManager` class (get/set/hash)
- **A1.2**: Write tests for `CacheManager`
- **A1.3**: Integrate into `BaseScraper.fetch()`

### A2: FirstCycling Grand Tour Index
- **A2.1**: Create `firstcycling.py` skeleton with rate limiting
- **A2.2**: Implement GT start list HTML parser
- **A2.3**: Write tests for parser
- **A2.4**: Implement `GTRelevanceIndex` class
- **A2.5**: Write tests for relevance check

### A3: Phase 1 Discovery Refactor
- **A3.1**: Update `DiscoveryService` constructor for year range
- **A3.2**: Implement Dual Seeding logic
- **A3.3**: Integrate `GTRelevanceIndex` filter
- **A3.4**: Write integration tests

### B1: Wikidata Resolver
- **B1.1**: Create `wikidata.py` with SPARQL query builder
- **B1.2**: Write tests with mocked responses
- **B1.3**: Implement sitelink extraction
- **B1.4**: Implement fallback logic

### B2: Data Model Updates
- **B2.1**: Add columns to SQLAlchemy models
- **B2.2**: Create Alembic migration
- **B2.3**: Update Pydantic schemas

### C1: Worker Infrastructure
- **C1.1**: Create `workers.py` with `SourceWorker` ABC
- **C1.2**: Implement `WikipediaWorker`
- **C1.3**: Write tests for `WikipediaWorker`
- **C1.4**: Implement `CyclingRankingWorker`
- **C1.5**: Write tests for `CyclingRankingWorker`
- **C1.6**: Implement `MemoireWorker`
- **C1.7**: Write tests for `MemoireWorker`

### C2: Phase 2 Enrichment Orchestration
- **C2.1**: Update `AssemblyOrchestrator` to call `WikidataResolver`
- **C2.2**: Implement parallel worker execution
- **C2.3**: Create `EnrichedTeamData` model
- **C2.4**: Write integration tests

### D1: Conflict Arbiter
- **D1.1**: Create `arbiter.py` with `ConflictArbiter` class
- **D1.2**: Design and implement arbitration prompt
- **D1.3**: Write tests with mocked LLM

### D2: Phase 2 Arbiter Integration
- **D2.1**: Implement conflict detection logic
- **D2.2**: Wire arbiter into Phase 2 flow
- **D2.3**: Write end-to-end tests

### E1: Phase 3 Wikipedia Context
- **E1.1**: Update `phase3.py` to retrieve history text
- **E1.2**: Update `DECIDE_LINEAGE_PROMPT`
- **E1.3**: Write tests

### F1: SSE Event Stream
- **F1.1**: Create `sse.py` utility
- **F1.2**: Implement stream endpoint
- **F1.3**: Emit events from Phase 2/3
- **F1.4**: Write API tests
