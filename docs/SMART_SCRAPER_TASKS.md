# Smart Scraper Task Checklist

**Status Legend:** `[ ]` = Pending | `[/]` = In Progress | `[x]` = Complete

---

## SLICE 1: Foundation (Day 1)

- [x] 1.1 Add dependencies to `requirements.txt`
- [x] 1.2 Create Alembic migration for prominence constraint
- [x] 1.3 Update `TeamSponsorLink` model validator
- [x] 1.4 Create "Smart Scraper" user seed script
- [x] **SLICE 1 COMMITTED**

---

## SLICE 2: LLM Client Layer (Day 2)

- [x] 2.1 Create `BaseLLMClient` protocol
- [x] 2.2 Implement `GeminiClient`
- [x] 2.3 Implement `DeepseekClient`
- [x] 2.4 Implement `LLMService` with fallback chain
- [x] 2.5 Add instructor patching to `LLMService`
- [x] **SLICE 2 COMMITTED**

---

## SLICE 3: Scraper Base Infrastructure (Day 3)


- [x] 3.1 Create `BaseScraper` abstract class
- [x] 3.2 Implement rate limiting with configurable delays
- [x] 3.3 Implement retry with exponential backoff
- [x] 3.4 Implement User-Agent rotation
- [x] **SLICE 3 COMMITTED**

---

## SLICE 4: CyclingFlash Scraper (Day 4-5)

- [x] 4.1 Create HTML fixture files
- [x] 4.2 Implement team list parser
- [x] 4.3 Implement team detail parser
- [x] 4.4 Implement "Previous Season" link follower
- [x] 4.5 Integrate into `CyclingFlashScraper` class
- [x] **SLICE 4 COMMITTED**

---

## SLICE 5: LLM Prompts - Data Extraction (Day 6)

- [x] 5.1 Define `ScrapedTeamData` Pydantic model
- [x] 5.2 Write `extract_team_data` prompt
- [x] 5.3 Integrate prompt into `LLMService`
- [x] 5.4 Test with CyclingFlash fixture HTML
- [x] **SLICE 5 COMMITTED**

---

## SLICE 6: Checkpoint System (Day 7)

- [x] 6.1 Design checkpoint JSON schema
- [x] 6.2 Implement `CheckpointManager` class
- [x] 6.3 Add checkpoint file location config
- [x] 6.4 Integrate with scraper loop
- [x] **SLICE 6 COMMITTED**

---

## SLICE 7: Phase 1 Orchestration - Discovery (Day 8-9)

- [x] 7.1 Implement sponsor name collector
- [x] 7.2 Define `SponsorResolution` Pydantic model
- [x] 7.3 Write `resolve_sponsor` LLM prompt
- [x] 7.4 Implement brand color search logic
- [x] 7.5 Wire Phase 1 into `SmartScraperService`
- [x] **SLICE 7 COMMITTED**

---

## SLICE 8: Phase 2 Orchestration - Team Assembly (Day 10-11)

- [x] 8.1 Implement team queue processor
- [x] 8.2 Implement sponsor mapping (string → UUID)
- [x] 8.3 Implement prominence calculation
- [x] 8.4 Integrate with AuditLogService for writes
- [x] 8.5 Wire Phase 2 into `SmartScraperService`
- [x] **SLICE 8 COMMITTED**

---

## SLICE 9: LLM Prompts - Lineage Decision (Day 12)

- [x] 9.1 Define `LineageDecision` Pydantic model
- [x] 9.2 Write `decide_lineage` prompt
- [x] 9.3 Test all event types
- [x] 9.4 Test confidence scoring
- [x] **SLICE 9 COMMITTED**

---

## SLICE 10: Phase 3 Orchestration - Lineage (Day 13)

- [x] 10.1 Implement orphan node detector
- [x] 10.2 Implement lineage decision pipeline
- [x] 10.3 Integrate with AuditLogService for LineageEvent
- [x] 10.4 Wire Phase 3 into `SmartScraperService`
- [x] **SLICE 10 COMMITTED**

---

## SLICE 11: Secondary/Tertiary Scrapers (Day 14-15)

- [x] 11.1 Implement `CyclingRankingScraper`
- [x] 11.2 Implement `WikidataScraper` (SPARQL)
- [x] 11.3 Implement `WikipediaScraper` (EN/DE/FR/IT/ES/NL)
- [x] 11.4 Implement `WaybackScraper`
- [x] 11.5 Implement `MemoireScraper`
- [x] **SLICE 11 COMMITTED**

---

## SLICE 12: Concurrent Workers (Day 16)

- [x] 12.1 Implement async worker pool
- [x] 12.2 Per-source rate limiting in workers
- [x] 12.3 Worker coordination
- [x] 12.4 Integrate into Phase 2+ orchestration
- [x] **SLICE 12 COMMITTED**

---

## SLICE 13: CLI Interface (Day 17)

- [x] 13.1 Implement argparse CLI
- [x] 13.2 Add --phase argument
- [x] 13.3 Add --tier argument
- [x] 13.4 Add --resume argument
- [x] 13.5 Add --dry-run argument
- [x] **SLICE 13 COMMITTED**

---

## SLICE 14: API Endpoint (Day 18)

- [x] 14.1 Create `POST /api/admin/scraper/start`
- [x] 14.2 Implement background task execution
- [x] 14.3 Create `GET /api/admin/scraper/status`
- [x] 14.4 Add admin-only authorization
- [x] **SLICE 14 COMMITTED**

---

## SLICE 15: End-to-End Testing & Polish (Day 19-20)

- [x] 15.1 Full E2E test (mock all sources)
- [x] 15.2 Test with real CyclingFlash (limited scope)
- [x] 15.3 Documentation (README section)
- [x] 15.4 Error handling review
- [x] **SLICE 15 COMMITTED**

---

## Final

- [x] Create Pull Request
- [ ] Code Review Complete
- [ ] Merged to Main
