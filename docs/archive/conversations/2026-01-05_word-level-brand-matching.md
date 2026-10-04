---
id: "bf6a5b70-beab-47a5-9b91-aaf7c7b58a92"
title: "Word-Level Brand Matching"
date: "2026-01-05T14:51:34.401033300Z"
workspace: "file:///c:/Users/fjung/Documents/DEV/chainlines"
---

# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

## SLICE 2.2: Word-Level Brand Matching

### Context

Add word-level brand matching to determine if all words in a team name match known brands in the database.

### Background

If we haven't seen this exact team name before, we check if all individual words (brands) are already known. If yes, we can skip the LLM call.

### Task

**Step 1: Write Tests First**

Add to `backend/tests/scraper/test_brand_matcher.py`:

```python
@pytest.mark.asyncio
async def test_brand_coverage_complete(db_session):
    """Test all words match existing brands - no LLM needed."""
    # Setup: Create brands "Lotto" and "Jumbo" in DB
    master = SponsorMaster(...)
    brand1 = SponsorBrand(master=master, brand_name="Lotto", ...)
    brand2 = SponsorBrand(master=master, brand_name="Jumbo", ...)
    db_session.add_all([master, brand1, brand2])
    await db_session.commit()
    
    matcher = BrandMatcherService(db_session)
    result = await matcher.analyze_words("Lotto Jumbo")
    
    assert result.needs_llm == False
    assert len(result.known_brands) == 2
    assert "Lotto" in result.known_brands
    assert "Jumbo" in result.known_brands
    assert len(result.unmatched_words) == 0

@pytest.mark.asyncio
async def test_brand_coverage_incomplete(db_session):
    """Test unknown words trigger LLM."""
    # Setup: Only create "Lotto" brand
    master = SponsorMaster(...)
    brand1 = SponsorBrand(master=master, brand_name="Lotto", ...)
    db_session.add(brand1)
    await db_session.commit()
    
    matcher = BrandMatcherService(db_session)
    result = await matcher.analyze_words("Lotto NL Jumbo")
    
    assert result.needs_llm == True
    assert "Lotto" in result.known_brands
    assert "NL" in result.unmatched_words
    assert "Jumbo" in result.unmatched_words

@pytest.mark.asyncio
async def test_brand_coverage_no_brands(db_session):
    """Test completely unknown team triggers LLM."""
    matcher = BrandMatcherService(db_session)
    result = await matcher.analyze_words("Unknown New Team")
    
    assert result.needs_llm == True
    assert len(result.known_brands) == 0
    assert len(result.unmatched_words) == 3
```

**Step 2: Implement Method**

Add to `backend/app/scraper/services/brand_matcher.py`:

```python
import re
from app.models.sponsor import SponsorBrand
from app.scraper.llm.models import BrandMatchResult

class BrandMatcherService:
    # ... existing methods ...
    
    async def analyze_words(self, team_name: str) -> BrandMatchResult:
        """
        Check if all words in team name match known brands.
        Returns analysis result indicating if LLM is needed.
        """
        # Tokenize: split on non-alphanumeric, keep words
        words = re.findall(r'\b[\w]+\b', team_name)
        
        known_brands = []
        unmatched_words = []
        
        for word in words:
            # Exact match against brand_name
            stmt = select(SponsorBrand).where(SponsorBrand.brand_name == word).limit(1)
            result = await self._session.execute(stmt)
            brand = result.scalar_one_or_none()
            
            if brand:
                known_brands.append(word)
            else:
                unmatched_words.append(word)
        
        needs_llm = len(unmatched_words) > 0
        
        logger.debug(
            f"Word analysis for '{team_name}': "
            f"{len(known_brands)} known, {len(unmatched_words)} unknown, "
            f"LLM needed: {needs_llm}"
        )
        
        return BrandMatchResult(
            known_brands=known_brands,
            unmatched_words=unmatched_words,
            needs_llm=needs_llm
        )
```

**Step 3: Verify**

```bash
pytest backend/tests/scraper/test_brand_matcher.py -v
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat(scraper): add word-level brand matching to BrandMatcher

- Implement analyze_words() method
- Tokenize team names and match against SponsorBrand table
- Return BrandMatchResult with known/unknown words
- Determine if LLM extraction is needed
- Tests for complete/incomplete/no coverage scenarios"
```

---


*User accepted the command `dir backend\app\scraper\llm\models.py backend\app\scraper\services\brand_matcher.py backend\tests\scraper\test_brand_matcher.py`*

*Viewed [brand_matcher.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/services/brand_matcher.py) *

*Viewed [models.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/scraper/llm/models.py) *

*Edited relevant file*

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_brand_matcher.py -v`*

*Checked command status*

*User accepted the command `pytest backend/tests/scraper/test_brand_matcher.py -v`*

*Checked command status*

*User accepted the command `pytest backend/tests/scraper/test_brand_matcher.py -v > test_output.txt 2>&1`*

*Checked command status*

*User accepted the command `pytest backend/tests/scraper/test_brand_matcher.py -v`*

*Checked command status*

*Viewed [sponsor.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/app/models/sponsor.py) *

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_brand_matcher.py -v`*

*Checked command status*

*Viewed [SMART_SCRAPER_TASKS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/SMART_SCRAPER_TASKS.md) *

*Viewed [PROGRESSIVE_SPONSOR_EXTRACTION_PROMPTS.md](file:///c:/Users/fjung/Documents/DEV/chainlines/docs/PROGRESSIVE_SPONSOR_EXTRACTION_PROMPTS.md) *

*User accepted the command `git checkout backend/tests/scraper/test_brand_matcher.py`*

*Viewed [test_brand_matcher.py](file:///c:/Users/fjung/Documents/DEV/chainlines/backend/tests/scraper/test_brand_matcher.py) *

*Edited relevant file*

*User accepted the command `pytest backend/tests/scraper/test_brand_matcher.py -v`*

*Checked command status*

*User accepted the command `git add -A
git commit -m "feat(scraper): add word-level brand matching to BrandMatcher

- Implement analyze_words() method
- Tokenize team names and match against SponsorBrand table
- Return BrandMatchResult with known/unknown words
- Determine if LLM extraction is needed
- Tests for complete/incomplete/no coverage scenarios"`*

*User accepted the command `del test_output.txt
git add -A
git commit --amend --no-edit`*