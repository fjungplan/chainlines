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

## Configuration

Environment variables:

- `GEMINI_API_KEY`: Google Gemini API key
- `DEEPSEEK_API_KEY`: Deepseek API key (fallback)

## Architecture

See `docs/SMART_SCRAPER_SPECIFICATION.md` for full details.
