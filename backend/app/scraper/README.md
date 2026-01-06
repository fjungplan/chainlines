# Smart Scraper

Bulk ingestion tool for cycling team historical data.

## Quick Start

### CLI Usage

```bash
# Run Phase 1: Discovery
python -m app.scraper.cli --phase 1 --tier 1

# Resume from checkpoint
python -m app.scraper.cli --phase 1 --resume

# Dry run (no DB writes)
python -m app.scraper.cli --phase 1 --dry-run
```

### API Usage

```bash
# Start scraper (admin only)
curl -X POST http://localhost:8000/api/admin/scraper/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phase": 1, "tier": "1"}'

# Check status
curl http://localhost:8000/api/admin/scraper/status/{task_id} \
  -H "Authorization: Bearer $TOKEN"
```

## Phases

1. **Discovery**: Spider CyclingFlash, collect team URLs and sponsor names
2. **Assembly**: Create TeamNodes, TeamEras, link sponsors
3. **Lineage**: Detect orphans, create LineageEvents

## Sponsor Extraction

The scraper uses LLM-based intelligent sponsor extraction with:

- **Two-level caching**: Team name cache + brand word matching
- **LLM integration**: Gemini (primary) + Deepseek (fallback)
- **Multi-tier resilience**: Exponential backoff + retry queue
- **Parent company tracking**: Links brands to sponsor masters

### How It Works

1. **Phase 1** (Discovery):
   - Parse team name from HTML
   - Check cache: exact team name match?
   - Check brands: all words known?
   - Call LLM if needed with context
   - Store SponsorInfo with parent companies

2. **Phase 2** (Assembly):
   - Create/update SponsorBrand records
   - Link to SponsorMaster (parent companies)
   - Create TeamSponsorLink with prominence

### Configuration

Set these environment variables:

```bash
GEMINI_API_KEY=your_gemini_key
DEEPSEEK_API_KEY=your_deepseek_key
```

### Testing

Run unit tests:
```bash
pytest backend/tests/scraper/test_brand_matcher.py -v
pytest backend/tests/scraper/test_sponsor_prompts.py -v
```

Run integration tests:
```bash
pytest backend/tests/integration/test_sponsor_extraction_e2e.py -v -m integration
```

See `docs/SPONSOR_EXTRACTION_MANUAL_VERIFICATION.md` for manual testing guide.

## Architecture

See `docs/SMART_SCRAPER_SPECIFICATION.md` for full details.
