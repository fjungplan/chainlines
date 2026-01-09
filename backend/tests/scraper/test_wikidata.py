import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.scraper.services.wikidata import WikidataResolver, WikidataResult


@pytest.fixture
def mock_cache():
    """Create a mock cache that returns None (cache miss)."""
    mock = Mock()
    mock.get.return_value = None
    return mock


@pytest.mark.asyncio
async def test_resolve_known_team(mock_cache):
    """Test that a known team returns a valid WikidataResult."""
    resolver = WikidataResolver(cache=mock_cache)
    
    # Mock internal methods directly
    with patch.object(resolver, '_search_entity', new_callable=AsyncMock) as mock_search, \
         patch.object(resolver, '_get_entity_details', new_callable=AsyncMock) as mock_details:
        
        mock_search.return_value = "Q20658729"
        mock_details.return_value = WikidataResult(
            qid="Q20658729",
            label="Peugeot cycling team",
            sitelinks={
                "en": "https://en.wikipedia.org/wiki/Peugeot_(cycling_team)",
                "fr": "https://fr.wikipedia.org/wiki/Équipe_cycliste_Peugeot",
                "nl": "https://nl.wikipedia.org/wiki/Peugeot_(wielerploeg)"
            }
        )
        
        result = await resolver.resolve("Peugeot cycling team")
        
        assert result is not None
        assert isinstance(result, WikidataResult)
        assert result.qid == "Q20658729"
        assert result.label == "Peugeot cycling team"
        assert "en" in result.sitelinks


@pytest.mark.asyncio
async def test_resolve_unknown_team(mock_cache):
    """Test that an unknown team returns None."""
    resolver = WikidataResolver(cache=mock_cache)
    
    with patch.object(resolver, '_search_entity', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = None  # No match found
        
        result = await resolver.resolve("XYZ Unknown Team")
        
        assert result is None


@pytest.mark.asyncio
async def test_extracts_wikipedia_urls(mock_cache):
    """Test that Wikipedia URLs for different languages are extracted correctly."""
    resolver = WikidataResolver(cache=mock_cache)
    
    with patch.object(resolver, '_search_entity', new_callable=AsyncMock) as mock_search, \
         patch.object(resolver, '_get_entity_details', new_callable=AsyncMock) as mock_details:
        
        mock_search.return_value = "Q20658729"
        mock_details.return_value = WikidataResult(
            qid="Q20658729",
            label="Peugeot cycling team",
            sitelinks={
                "en": "https://en.wikipedia.org/wiki/Peugeot_(cycling_team)",
                "fr": "https://fr.wikipedia.org/wiki/Équipe_cycliste_Peugeot",
                "nl": "https://nl.wikipedia.org/wiki/Peugeot_(wielerploeg)"
            }
        )
        
        result = await resolver.resolve("Peugeot cycling team")
        
        assert result is not None
        assert len(result.sitelinks) >= 3
        assert "en.wikipedia.org" in result.sitelinks["en"]
        assert "fr.wikipedia.org" in result.sitelinks["fr"]
        assert "nl.wikipedia.org" in result.sitelinks["nl"]


@pytest.mark.asyncio
async def test_respects_cache(mock_cache):
    """Test that cached results are returned without making an HTTP request."""
    # Setup cache to return a stored result
    cached_data = WikidataResult(
        qid="Q12345", 
        label="Cached Team", 
        sitelinks={"en": "http://en.wiki"}
    ).model_dump_json()
    
    mock_cache.get.return_value = cached_data
    
    resolver = WikidataResolver(cache=mock_cache)
    
    with patch.object(resolver, '_search_entity', new_callable=AsyncMock) as mock_search:
        result = await resolver.resolve("Cached Team")
        
        assert result is not None
        assert result.qid == "Q12345"
        assert result.label == "Cached Team"
        
        # Verify cache was checked
        mock_cache.get.assert_called_once()
        # Verify search was NOT called (cache hit)
        mock_search.assert_not_called()


@pytest.mark.asyncio
async def test_writes_to_cache(mock_cache):
    """Test that successful API results are written to cache."""
    resolver = WikidataResolver(cache=mock_cache)
    
    with patch.object(resolver, '_search_entity', new_callable=AsyncMock) as mock_search, \
         patch.object(resolver, '_get_entity_details', new_callable=AsyncMock) as mock_details:
        
        mock_search.return_value = "Q20658729"
        mock_details.return_value = WikidataResult(
            qid="Q20658729",
            label="Peugeot cycling team",
            sitelinks={"en": "https://en.wikipedia.org/wiki/Peugeot"}
        )
        
        await resolver.resolve("Peugeot cycling team")
        
        mock_cache.set.assert_called_once()
        args, kwargs = mock_cache.set.call_args
        assert "wikidata_api" in args[0]  # key
        assert "Q20658729" in args[1]  # content
        assert kwargs.get("domain") == "wikidata"
