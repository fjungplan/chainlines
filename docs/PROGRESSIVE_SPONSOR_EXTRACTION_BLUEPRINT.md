# Progressive Sponsor Extraction - Implementation Blueprint

**Status**: Ready for Implementation  
**Created**: 2026-01-05  
**Specification**: See `PROGRESSIVE_SPONSOR_EXTRACTION.md`

---

## Phase 1: Foundation - Pydantic Models

### Slice 1.1: Create LLM Response Models
- **File**: `backend/app/scraper/llm/models.py` (NEW)
- **Models**: `SponsorInfo`, `SponsorExtractionResult`, `BrandMatchResult`
- **Tests**: `backend/tests/scraper/test_llm_models.py`
- **Risk**: Low (just data models)
- **Integration**: Export in `__init__.py`

### Slice 1.2: Update ScrapedTeamData Model
- **File**: `backend/app/scraper/sources/cyclingflash.py`
- **Change**: `sponsors: List[str]` → `sponsors: List[SponsorInfo]`
- **Add**: `extraction_confidence` field
- **Tests**: Update `test_cyclingflash.py` 
- **Risk**: Medium (breaks existing code)
- **Integration**: Update parser to use SponsorInfo

---

## Phase 2: BrandMatcher Service

### Slice 2.1: Team Name Cache (DB Lookup)
- **File**: `backend/app/scraper/services/brand_matcher.py` (NEW)
- **Class**: `BrandMatcherService`
- **Method**: `check_team_name()`
- **Tests**: `test_brand_matcher.py::test_team_name_cache_*`
- **Risk**: Low (read-only DB queries)
- **Integration**: Export in services `__init__.py`

### Slice 2.2: Word-Level Brand Matching
- **File**: Same as 2.1
- **Method**: `analyze_words()`
- **Tests**: `test_brand_matcher.py::test_brand_coverage_*`
- **Risk**: Low (read-only)
- **Integration**: Called by team name cache fallback

---

## Phase 3: LLM Integration

### Slice 3.1: Sponsor Extraction Prompt
- **File**: `backend/app/scraper/llm/prompts.py`
- **Add**: `SPONSOR_EXTRACTION_PROMPT` constant
- **Method**: `extract_sponsors_from_name()`
- **Tests**: Mock-based test in `test_prompts.py`
- **Risk**: Low (isolated method)
- **Integration**: Add to ScraperPrompts class

---

## Phase 4: Phase 1 Integration

### Slice 4.1: Update DiscoveryService Constructor
- **File**: `backend/app/scraper/orchestration/phase1.py`
- **Change**: Add `session`, `llm_prompts` parameters
- **Add**: Initialize `_brand_matcher`
- **Tests**: Update `test_phase1.py` fixtures
- **Risk**: Low (backward compatible)
- **Integration**: CLI/main must pass new params

### Slice 4.2: Sponsor Extraction Method
- **File**: Same as 4.1
- **Method**: `_extract_sponsors()` with two-level caching
- **Tests**: `test_phase1.py::test_extract_sponsors_*`
- **Risk**: Medium (LLM calls)
- **Integration**: Called during team discovery

### Slice 4.3: Integrate into Discovery Loop
- **File**: Same as 4.1
- **Change**: Call `_extract_sponsors()` in discovery loop
- **Tests**: Integration test with full flow
- **Risk**: High (changes core scraping)
- **Integration**: Updates ScrapedTeamData with SponsorInfo

---

## Phase 5: Phase 2 Updates

### Slice 5.1: Update TeamAssemblyService
- **File**: `backend/app/scraper/orchestration/phase2.py`
- **Change**: Handle `SponsorInfo` instead of `str`
- **Method**: Update `_create_sponsor_links()`
- **Tests**: `test_phase2.py::test_assembly_*`
- **Risk**: Medium (database writes)
- **Integration**: Creates/updates SponsorBrand records

---

## Phase 6: Error Handling

### Slice 6.1: Retry Queue Implementation
- **File**: `backend/app/scraper/orchestration/phase1.py`
- **Add**: `_retry_queue` attribute
- **Method**: `_process_retry_queue()`
- **Tests**: `test_phase1.py::test_retry_*`
- **Risk**: Low (fallback mechanism)
- **Integration**: Called at end of year processing

### Slice 6.2: Multi-Tier Resilience
- **File**: Same as 6.1
- **Method**: `_extract_with_resilience()`
- **Tests**: `test_phase1.py::test_resilience_*`
- **Risk**: Medium (complex error handling)
- **Integration**: Wraps `_extract_sponsors()`

---

## Phase 7: Integration Testing

### Slice 7.1: End-to-End Tests
- **File**: `backend/tests/integration/test_sponsor_extraction_e2e.py` (NEW)
- **Tests**: Full flow from scraping to DB storage
- **Risk**: Low (validation only)
- **Integration**: Verifies all slices work together

### Slice 7.2: Manual Verification
- **Actions**: Run scraper on 2024 WorldTour sample
- **Verify**: Sponsor accuracy, LLM call count
- **Risk**: Low (observation only)
- **Integration**: Final validation

---

## Iteration Refinement

**Round 1 Assessment:**
- Slices 1-3: ✅ Right-sized (isolated, testable)
- Slice 4.3: ❌ Too big (core loop changes)
- Slice 5.1: ✅ Medium complexity, well-scoped

**Round 2 Refinement:**
Split 4.3 into:
- 4.3a: Add extraction to discovery (equipment sponsors only)
- 4.3b: Merge title + equipment sponsors

**Round 2 Assessment:**
- All slices: ✅ Small, incremental, testable
- Dependencies: ✅ Clear progression
- Integration: ✅ Each step wires to previous

**Final Blueprint: 11 implementation slices**

---

## Slice Dependencies

```
1.1 (Models) ──┐
               ├──> 1.2 (Update ScrapedTeamData)
               │
2.1 (Cache) ───┼──> 2.2 (Word Match) ──┐
               │                        │
3.1 (Prompts)──┴────────────────────────┼──> 4.1 (Constructor) 
                                        │
                                        ├──> 4.2 (Extract Method)
                                        │
                                        ├──> 4.3a (Equipment)
                                        │
                                        └──> 4.3b (Title Merge)
                                             │
                                             ├──> 5.1 (Phase 2)
                                             │
                                             ├──> 6.1 (Retry Queue)
                                             │
                                             ├──> 6.2 (Resilience)
                                             │
                                             └──> 7.1, 7.2 (Testing)
```

---

## Risk Mitigation

**High Risk Slices:**
- 4.3a, 4.3b (Core loop changes)
  - Mitigation: Extensive unit tests, feature flag

**Medium Risk Slices:**
- 1.2 (Breaking change)
  - Mitigation: Update all tests first
- 4.2 (LLM integration)
  - Mitigation: Mock LLM in tests
- 5.1 (DB writes)
  - Mitigation: Transaction rollback in tests

**Low Risk Slices:**
- 1.1, 2.1, 2.2, 3.1 (Isolated, read-only)

---

## Testing Strategy Per Slice

Each slice follows TDD:
1. Write failing tests first
2. Implement minimum code to pass
3. Refactor
4. Integration test
5. Commit

**Test Coverage Target:** 95%+

---

## Ready for Prompt Generation ✅
