# Smart Scraper Task Checklist

**Status Legend:** `[ ]` = Pending | `[/]` = In Progress | `[x]` = Complete

---

## SLICE 1: Foundation (Day 1)

- [ ] 1.1 Add dependencies to `requirements.txt`
- [ ] 1.2 Create Alembic migration for prominence constraint
- [ ] 1.3 Update `TeamSponsorLink` model validator
- [ ] 1.4 Create "Smart Scraper" user seed script
- [ ] **SLICE 1 COMMITTED**

---

## SLICE 2: LLM Client Layer (Day 2)

- [ ] 2.1 Create `BaseLLMClient` protocol
- [ ] 2.2 Implement `GeminiClient`
- [ ] 2.3 Implement `DeepseekClient`
- [ ] 2.4 Implement `LLMService` with fallback chain
- [ ] 2.5 Add instructor patching to `LLMService`
- [ ] **SLICE 2 COMMITTED**

---

## SLICE 3: Scraper Base Infrastructure (Day 3)

- [ ] 3.1 Create `BaseScraper` abstract class
- [ ] 3.2 Implement rate limiting with configurable delays
- [ ] 3.3 Implement retry with exponential backoff
- [ ] 3.4 Implement User-Agent rotation
- [ ] **SLICE 3 COMMITTED**

---

## SLICE 4: CyclingFlash Scraper (Day 4-5)

- [ ] 4.1 Create HTML fixture files
- [ ] 4.2 Implement team list parser
- [ ] 4.3 Implement team detail parser
- [ ] 4.4 Implement "Previous Season" link follower
- [ ] 4.5 Integrate into `CyclingFlashScraper` class
- [ ] **SLICE 4 COMMITTED**

---

## SLICE 5: LLM Prompts - Data Extraction (Day 6)

- [ ] 5.1 Define `ScrapedTeamData` Pydantic model
- [ ] 5.2 Write `extract_team_data` prompt
- [ ] 5.3 Integrate prompt into `LLMService`
- [ ] 5.4 Test with CyclingFlash fixture HTML
- [ ] **SLICE 5 COMMITTED**

---

## SLICE 6: Checkpoint System (Day 7)

- [ ] 6.1 Design checkpoint JSON schema
- [ ] 6.2 Implement `CheckpointManager` class
- [ ] 6.3 Add checkpoint file location config
- [ ] 6.4 Integrate with scraper loop
- [ ] **SLICE 6 COMMITTED**

---

## SLICE 7: Phase 1 Orchestration - Discovery (Day 8-9)

- [ ] 7.1 Implement sponsor name collector
- [ ] 7.2 Define `SponsorResolution` Pydantic model
- [ ] 7.3 Write `resolve_sponsor` LLM prompt
- [ ] 7.4 Implement brand color search logic
- [ ] 7.5 Wire Phase 1 into `SmartScraperService`
- [ ] **SLICE 7 COMMITTED**

---

## SLICE 8: Phase 2 Orchestration - Team Assembly (Day 10-11)

- [ ] 8.1 Implement team queue processor
- [ ] 8.2 Implement sponsor mapping (string → UUID)
- [ ] 8.3 Implement prominence calculation
- [ ] 8.4 Integrate with AuditLogService for writes
- [ ] 8.5 Wire Phase 2 into `SmartScraperService`
- [ ] **SLICE 8 COMMITTED**

---

## SLICE 9: LLM Prompts - Lineage Decision (Day 12)

- [ ] 9.1 Define `LineageDecision` Pydantic model
- [ ] 9.2 Write `decide_lineage` prompt
- [ ] 9.3 Test all event types
- [ ] 9.4 Test confidence scoring
- [ ] **SLICE 9 COMMITTED**

---

## SLICE 10: Phase 3 Orchestration - Lineage (Day 13)

- [ ] 10.1 Implement orphan node detector
- [ ] 10.2 Implement lineage decision pipeline
- [ ] 10.3 Integrate with AuditLogService for LineageEvent
- [ ] 10.4 Wire Phase 3 into `SmartScraperService`
- [ ] **SLICE 10 COMMITTED**

---

## SLICE 11: Secondary/Tertiary Scrapers (Day 14-15)

- [ ] 11.1 Implement `CyclingRankingScraper`
- [ ] 11.2 Implement `WikidataScraper` (SPARQL)
- [ ] 11.3 Implement `WikipediaScraper` (EN/DE/FR/IT/ES/NL)
- [ ] 11.4 Implement `WaybackScraper`
- [ ] 11.5 Implement `MemoireScraper`
- [ ] **SLICE 11 COMMITTED**

---

## SLICE 12: Concurrent Workers (Day 16)

- [ ] 12.1 Implement async worker pool
- [ ] 12.2 Per-source rate limiting in workers
- [ ] 12.3 Worker coordination
- [ ] 12.4 Integrate into Phase 2+ orchestration
- [ ] **SLICE 12 COMMITTED**

---

## SLICE 13: CLI Interface (Day 17)

- [ ] 13.1 Implement argparse CLI
- [ ] 13.2 Add --phase argument
- [ ] 13.3 Add --tier argument
- [ ] 13.4 Add --resume argument
- [ ] 13.5 Add --dry-run argument
- [ ] **SLICE 13 COMMITTED**

---

## SLICE 14: API Endpoint (Day 18)

- [ ] 14.1 Create `POST /api/admin/scraper/start`
- [ ] 14.2 Implement background task execution
- [ ] 14.3 Create `GET /api/admin/scraper/status`
- [ ] 14.4 Add admin-only authorization
- [ ] **SLICE 14 COMMITTED**

---

## SLICE 15: End-to-End Testing & Polish (Day 19-20)

- [ ] 15.1 Full E2E test (mock all sources)
- [ ] 15.2 Test with real CyclingFlash (limited scope)
- [ ] 15.3 Documentation (README section)
- [ ] 15.4 Error handling review
- [ ] **SLICE 15 COMMITTED**

---

## Final

- [ ] Create Pull Request
- [ ] Code Review Complete
- [ ] Merged to Main
