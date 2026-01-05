# Smart Scraper Implementation Breakdown

**Version:** 1.0  
**Date:** 2026-01-04  
**Parent Document:** [SMART_SCRAPER_SPECIFICATION.md](./SMART_SCRAPER_SPECIFICATION.md)

---

## Iteration 1: High-Level Chunks

### Chunk A: Foundation & Infrastructure
- Database migrations
- System user setup
- Dependencies installation
- Base classes/interfaces

### Chunk B: LLM Service Layer
- Gemini/Deepseek client setup
- Instructor integration
- Core prompts (extract, decide, resolve)

### Chunk C: Source Scrapers
- CyclingFlash scraper
- CyclingRanking scraper
- Tertiary source scrapers (Wiki, Archive.org)

### Chunk D: Orchestration Layer
- SmartScraperService
- Checkpointing/Resume
- Concurrent workers

### Chunk E: Entry Points
- CLI interface
- API endpoint

---

## Iteration 2: Breaking Chunks into Steps

### Chunk A: Foundation & Infrastructure

#### A.1 Dependencies
- Add `instructor`, `google-generativeai`, `openai` to `requirements.txt`
- Verify installation

#### A.2 Database Migration - Prominence Constraint
- Create Alembic migration to relax `check_prominence_range` (allow >= 0)
- Update SQLAlchemy model validator
- Test migration up/down

#### A.3 System Bot User
- Create seed script for "Smart Scraper" user with fixed UUID
- Add to existing seed workflow
- Test user exists after seeding

---

### Chunk B: LLM Service Layer

#### B.1 LLM Client Abstraction
- Create `BaseLLMClient` interface
- Implement `GeminiClient` 
- Implement `DeepseekClient`
- Fallback chain logic

#### B.2 Instructor Integration
- Setup Pydantic response models for LLM outputs
- Create `LLMService` class with instructor patching
- Test structured output extraction

#### B.3 Core Prompts - Team Data Extraction
- Implement `extract_team_data(html) -> ScrapedTeamData`
- Write unit tests with mocked HTML
- Validate Pydantic parsing

#### B.4 Core Prompts - Lineage Decision
- Implement `decide_lineage(eras, data) -> LineageDecision`
- Test all event types (LEGAL_TRANSFER, MERGE, SPLIT, SPIRITUAL_SUCCESSION)
- Validate confidence scoring

#### B.5 Core Prompts - Sponsor Resolution
- Implement `resolve_sponsor(names) -> List[SponsorResolution]`
- Include brand color determination
- Test Master vs Brand classification

---

### Chunk C: Source Scrapers

#### C.1 Base Scraper Infrastructure
- Create `BaseScraper` abstract class
- Rate limiting logic (configurable per-source)
- Retry with exponential backoff
- User-Agent rotation

#### C.2 CyclingFlash Scraper
- Implement `CyclingFlashScraper(BaseScraper)`
- Parse team list page
- Parse individual team page
- Follow "Previous Season" links
- Unit tests with saved HTML fixtures

#### C.3 CyclingRanking Scraper
- Implement `CyclingRankingScraper(BaseScraper)`
- Parse team data
- Cross-reference logic
- Unit tests

#### C.4 Wikipedia/Wikidata Scraper (Multi-Language)
- Implement SPARQL queries for Wikidata
- Wikipedia History section parser
- Support 6 language versions: EN, DE, FR, IT, ES, NL
- Unit tests

#### C.5 Archive.org Wayback Scraper
- Implement Wayback API client
- Memoire du Cyclisme parser
- "Newest snapshot" logic
- Unit tests

---

### Chunk D: Orchestration Layer

#### D.1 Checkpoint System
- Design checkpoint schema (JSON or DB table)
- Implement save/load checkpoint
- Resume from last position
- Unit tests

#### D.2 SmartScraperService - Phase 1
- Implement discovery loop (CyclingFlash spider)
- Sponsor extraction pipeline
- Integration with LLMService for sponsor resolution
- Integration test

#### D.3 SmartScraperService - Phase 2
- Team queue processing
- TeamNode/TeamEra creation via AuditLog
- Sponsor prominence calculation
- Integration test

#### D.4 SmartScraperService - Phase 3
- Orphan node detection
- Lineage decision pipeline
- LineageEvent creation via AuditLog
- Integration test

#### D.5 Concurrent Source Workers
- Implement async worker pool
- Per-source rate limiting
- Coordination between workers
- Integration test

---

### Chunk E: Entry Points

#### E.1 CLI Interface
- Argparse-based CLI
- Phase selection (--phase 1/2/3)
- Tier selection (--tier wt/pt/ct)
- Resume from checkpoint (--resume)
- Dry-run mode (--dry-run)

#### E.2 API Endpoint
- `POST /api/admin/scraper/start` endpoint
- Background task execution
- Status polling endpoint
- Admin-only authorization

---

## Iteration 3: Right-Sizing Assessment

**Too Small (Merge Up):**
- A.1 (Dependencies) can be done alongside A.2 (Migration)
- B.1 + B.2 can be combined (both are LLM client setup)

**Too Large (Split Down):**
- D.2, D.3, D.4 (Phase orchestration) are large - consider splitting DB integration from orchestration logic
- C.2 (CyclingFlash) - split parsing from spidering

**Dependencies:**
```
A.1 → A.2 → A.3 (Foundation must be first)
     ↓
B.1 → B.2 → B.3 → B.4 → B.5 (LLM layer builds progressively)
     ↓
C.1 → C.2 → C.3 → C.4 → C.5 (Scrapers share base)
     ↓
D.1 → D.2 → D.3 → D.4 → D.5 (Orchestration depends on scrapers + LLM)
     ↓
E.1 + E.2 (Entry points depend on orchestration)
```

---

## Iteration 4: Final Right-Sized Steps

### SLICE 1: Foundation (Day 1)
**Goal:** Get infrastructure in place, unblock all other work.

| Step | Task | Test |
|------|------|------|
| 1.1 | Add dependencies to `requirements.txt` | `pip install -r requirements.txt` passes |
| 1.2 | Create Alembic migration for prominence constraint | Migration up/down works |
| 1.3 | Update `TeamSponsorLink` model validator | Unit test for 0% prominence |
| 1.4 | Create "Smart Scraper" user seed script | Integration test: user exists |

**Commit:** `feat(scraper): add foundation infrastructure`

---

### SLICE 2: LLM Client Layer (Day 2)
**Goal:** Establish LLM connectivity with fallback.

| Step | Task | Test |
|------|------|------|
| 2.1 | Create `BaseLLMClient` protocol | Type checking passes |
| 2.2 | Implement `GeminiClient` | Live test with simple prompt |
| 2.3 | Implement `DeepseekClient` | Live test with simple prompt |
| 2.4 | Implement `LLMService` with fallback chain | Unit test: fallback triggers on error |
| 2.5 | Add instructor patching to `LLMService` | Unit test: structured output works |

**Commit:** `feat(scraper): add LLM client layer with fallback`

---

### SLICE 3: Scraper Base Infrastructure (Day 3)
**Goal:** Reusable scraper foundation.

| Step | Task | Test |
|------|------|------|
| 3.1 | Create `BaseScraper` abstract class | N/A (abstract) |
| 3.2 | Implement rate limiting with configurable delays | Unit test: delays respected |
| 3.3 | Implement retry with exponential backoff | Unit test: retries work |
| 3.4 | Implement User-Agent rotation | Unit test: headers rotate |

**Commit:** `feat(scraper): add base scraper infrastructure`

---

### SLICE 4: CyclingFlash Scraper (Day 4-5)
**Goal:** Primary source scraper working.

| Step | Task | Test |
|------|------|------|
| 4.1 | Create HTML fixture files (saved pages) | N/A (test data) |
| 4.2 | Implement team list parser | Unit test with fixture |
| 4.3 | Implement team detail parser | Unit test with fixture |
| 4.4 | Implement "Previous Season" link follower | Unit test with fixture |
| 4.5 | Integrate into `CyclingFlashScraper` class | Integration test (mocked HTTP) |

**Commit:** `feat(scraper): add CyclingFlash scraper`

---

### SLICE 5: LLM Prompts - Data Extraction (Day 6)
**Goal:** LLM can extract structured data from HTML.

| Step | Task | Test |
|------|------|------|
| 5.1 | Define `ScrapedTeamData` Pydantic model | Unit test: validation |
| 5.2 | Write `extract_team_data` prompt | Manual test with real HTML |
| 5.3 | Integrate prompt into `LLMService` | Unit test with mocked LLM |
| 5.4 | Test with CyclingFlash fixture HTML | Integration test |

**Commit:** `feat(scraper): add team data extraction prompt`

---

### SLICE 6: Checkpoint System (Day 7)
**Goal:** Safe resume capability.

| Step | Task | Test |
|------|------|------|
| 6.1 | Design checkpoint JSON schema | N/A (design) |
| 6.2 | Implement `CheckpointManager` class | Unit test: save/load |
| 6.3 | Add checkpoint file location config | Config test |
| 6.4 | Integrate with scraper loop | Integration test: resume works |

**Commit:** `feat(scraper): add checkpoint/resume system`

---

### SLICE 7: Phase 1 Orchestration - Discovery (Day 8-9)
**Goal:** Complete discovery phase working.

| Step | Task | Test |
|------|------|------|
| 7.1 | Implement sponsor name collector | Unit test |
| 7.2 | Define `SponsorResolution` Pydantic model | Unit test |
| 7.3 | Write `resolve_sponsor` LLM prompt | Manual test |
| 7.4 | Implement brand color search logic | Unit test |
| 7.5 | Wire Phase 1 into `SmartScraperService` | Integration test |

**Commit:** `feat(scraper): add Phase 1 discovery orchestration`

---

### SLICE 8: Phase 2 Orchestration - Team Assembly (Day 10-11)
**Goal:** Create TeamNodes and TeamEras from scraped data.

| Step | Task | Test |
|------|------|------|
| 8.1 | Implement team queue processor | Unit test |
| 8.2 | Implement sponsor mapping (string → UUID) | Unit test |
| 8.3 | Implement prominence calculation | Unit test (all rules) |
| 8.4 | Integrate with AuditLogService for writes | Integration test |
| 8.5 | Wire Phase 2 into `SmartScraperService` | Integration test |

**Commit:** `feat(scraper): add Phase 2 team assembly orchestration`

---

### SLICE 9: LLM Prompts - Lineage Decision (Day 12)
**Goal:** LLM can determine lineage relationships.

| Step | Task | Test |
|------|------|------|
| 9.1 | Define `LineageDecision` Pydantic model | Unit test |
| 9.2 | Write `decide_lineage` prompt | Manual test |
| 9.3 | Test all event types | Unit tests per type |
| 9.4 | Test confidence scoring | Unit test |

**Commit:** `feat(scraper): add lineage decision prompt`

---

### SLICE 10: Phase 3 Orchestration - Lineage (Day 13)
**Goal:** Connect orphan nodes with lineage events.

| Step | Task | Test |
|------|------|------|
| 10.1 | Implement orphan node detector | Unit test |
| 10.2 | Implement lineage decision pipeline | Integration test |
| 10.3 | Integrate with AuditLogService for LineageEvent | Integration test |
| 10.4 | Wire Phase 3 into `SmartScraperService` | Integration test |

**Commit:** `feat(scraper): add Phase 3 lineage orchestration`

---

### SLICE 11: Secondary/Tertiary Scrapers (Day 14-15)
**Goal:** Enrichment sources working.

| Step | Task | Test |
|------|------|------|
| 11.1 | Implement `CyclingRankingScraper` | Unit test with fixture |
| 11.2 | Implement `WikidataScraper` (SPARQL) | Unit test |
| 11.3 | Implement `WikipediaScraper` (EN/DE/FR/IT/ES/NL) | Unit test with fixtures |
| 11.4 | Implement `WaybackScraper` | Unit test |
| 11.5 | Implement `MemoireScraper` | Unit test with fixture |

**Commit:** `feat(scraper): add enrichment source scrapers`

---

### SLICE 12: Concurrent Workers (Day 16)
**Goal:** Parallel source fetching.

| Step | Task | Test |
|------|------|------|
| 12.1 | Implement async worker pool | Unit test |
| 12.2 | Per-source rate limiting in workers | Unit test |
| 12.3 | Worker coordination | Integration test |
| 12.4 | Integrate into Phase 2+ orchestration | Integration test |

**Commit:** `feat(scraper): add concurrent source workers`

---

### SLICE 13: CLI Interface (Day 17)
**Goal:** Run scraper from command line.

| Step | Task | Test |
|------|------|------|
| 13.1 | Implement argparse CLI | Unit test |
| 13.2 | Add --phase argument | CLI test |
| 13.3 | Add --tier argument | CLI test |
| 13.4 | Add --resume argument | CLI test |
| 13.5 | Add --dry-run argument | CLI test |

**Commit:** `feat(scraper): add CLI interface`

---

### SLICE 14: API Endpoint (Day 18)
**Goal:** Trigger scraper from admin panel.

| Step | Task | Test |
|------|------|------|
| 14.1 | Create `POST /api/admin/scraper/start` | API test |
| 14.2 | Implement background task execution | Integration test |
| 14.3 | Create `GET /api/admin/scraper/status` | API test |
| 14.4 | Add admin-only authorization | Security test |

**Commit:** `feat(scraper): add API endpoint`

---

### SLICE 15: End-to-End Testing & Polish (Day 19-20)
**Goal:** Production-ready scraper.

| Step | Task | Test |
|------|------|------|
| 15.1 | Full E2E test (mock all sources) | E2E test |
| 15.2 | Test with real CyclingFlash (limited scope) | Manual test |
| 15.3 | Documentation (README section) | N/A |
| 15.4 | Error handling review | Code review |

**Commit:** `feat(scraper): finalize with E2E tests and docs`

---

## Summary

| Slice | Focus | Days | Dependencies |
|-------|-------|------|--------------|
| 1 | Foundation | 1 | None |
| 2 | LLM Client | 1 | Slice 1 |
| 3 | Scraper Base | 1 | Slice 1 |
| 4 | CyclingFlash | 2 | Slice 3 |
| 5 | Data Extraction | 1 | Slice 2, 4 |
| 6 | Checkpointing | 1 | Slice 1 |
| 7 | Phase 1 | 2 | Slice 5, 6 |
| 8 | Phase 2 | 2 | Slice 7 |
| 9 | Lineage Prompt | 1 | Slice 2 |
| 10 | Phase 3 | 1 | Slice 8, 9 |
| 11 | Enrichment Scrapers | 2 | Slice 3 |
| 12 | Concurrent Workers | 1 | Slice 11 |
| 13 | CLI | 1 | Slice 10 |
| 14 | API | 1 | Slice 10 |
| 15 | E2E & Polish | 2 | All |

**Total: ~20 working days**
