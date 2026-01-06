# Sponsor Extraction - Manual Verification Guide

## Prerequisites

- Database with test data
- LLM API keys configured (Gemini & Deepseek)
- Scraper CLI working

## Test 1: Single Team Extraction

**Objective**: Verify sponsor extraction for a known team

```bash
python -m app.scraper.cli \
  --phase 1 \
  --tier 1 \
  --start-year 2024 \
  --end-year 2024 \
  --dry-run
```

**Expected Results**:
- Logs show "Calling LLM for..." messages
- Team sponsors extracted with confidence scores
- DB contains TeamEra with SponsorBrand links

**Verification**:
```sql
SELECT 
    te.registered_name,
    sb.brand_name,
    sm.legal_name as parent_company,
    tsl.prominence_percentage
FROM team_eras te
JOIN team_sponsor_links tsl ON te.era_id = tsl.era_id
JOIN sponsor_brands sb ON tsl.brand_id = sb.brand_id
LEFT JOIN sponsor_masters sm ON sb.master_id = sm.master_id
WHERE te.season_year = 2024
ORDER BY te.registered_name, tsl.prominence_percentage DESC;
```

## Test 2: Cache Verification

**Objective**: Verify team name caching works

1. Run scraper for 2024 (first time)
2. Run scraper for 2024 again (should use cache)

**Expected Results**:
- First run: "LLM extraction complete" logs
- Second run: "Team name cache HIT" logs
- No duplicate LLM calls for same team names

## Test 3: Known Test Cases

Verify these specific extractions:

| Team Name | Expected Sponsors | Parent Company | Notes |
|-----------|------------------|----------------|-------|
| "Bahrain Victorious" | ["Bahrain"] | None | "Victorious" is descriptor |
| "Ineos Grenadiers" | ["Ineos Grenadier"] | "INEOS Group" | Multi-word brand |
| "UAE Team Emirates" | ["UAE", "Emirates"] | None | Multiple sponsors |
| "Lotto NL Jumbo" | ["Lotto NL", "Jumbo"] | None | Regional variant |

## Test 4: Fallback Behavior

**Objective**: Verify pattern fallback when LLM fails

1. Temporarily disable LLM API keys
2. Run scraper
3. Verify pattern extraction used with low confidence

**Expected Results**:
- Logs show "No LLM/BrandMatcher available, using pattern fallback"
- Sponsors extracted with confidence < 0.5
- Scraping completes without crashing

## Test 5: Performance

**Objective**: Verify LLM call optimization

Run scraper for multiple years and monitor:
- Number of LLM calls
- Cache hit rate
- Total scraping time

**Expected**:
- ~80% cache hit rate on subsequent runs
- < 1 LLM call per unique team name
