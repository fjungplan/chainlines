import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from app.scraper.services.wikidata import WikidataResolver, WikidataResult

# Mock response for search API (wbsearchentities)
MOCK_SEARCH_RESPONSE_PEUGEOT = {
    "search": [
        {
            "id": "Q20658729",
            "label": "Peugeot cycling team",
            "description": "French cycling team"
        }
    ]
}

# Mock response for entity API (wbgetentities)
MOCK_ENTITY_RESPONSE_PEUGEOT = {
    "entities": {
        "Q20658729": {
            "labels": {"en": {"value": "Peugeot cycling team"}},
            "sitelinks": {
                "enwiki": {"title": "Peugeot (cycling team)"},
                "frwiki": {"title": "Équipe cycliste Peugeot"},
                "nlwiki": {"title": "Peugeot (wielerploeg)"}
            }
        }
    }
}

# Mock response for unknown team
MOCK_SEARCH_RESPONSE_EMPTY = {
    "search": []
}

@pytest.fixture
def mock_cache():
    # CacheManager methods are synchronous
    mock = Mock()
    mock.get.return_value = None
    return mock

def create_mock_response(data):
    """Helper to create a mock response object."""
    mock_resp = Mock()
    mock_resp.json.return_value = data
    mock_resp.raise_for_status = Mock()
    return mock_resp

@pytest.mark.asyncio
async def test_resolve_known_team(mock_cache):
    """Test that a known team returns a valid WikidataResult."""
    with patch("httpx.AsyncClient") as mock_client:
        # Setup mock to return search then entity response
        mock_get = AsyncMock()
        mock_get.side_effect = [
            create_mock_response(MOCK_SEARCH_RESPONSE_PEUGEOT),
            create_mock_response(MOCK_ENTITY_RESPONSE_PEUGEOT)
        ]
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        resolver = WikidataResolver(cache=mock_cache)
        result = await resolver.resolve("Peugeot cycling team")
        
        assert result is not None
        assert isinstance(result, WikidataResult)
        assert result.qid == "Q20658729"
        assert result.label == "Peugeot cycling team"
        assert "en" in result.sitelinks
        assert "Peugeot" in result.sitelinks["en"]

@pytest.mark.asyncio
async def test_resolve_unknown_team(mock_cache):
    """Test that an unknown team returns None."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.return_value = create_mock_response(MOCK_SEARCH_RESPONSE_EMPTY)
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        resolver = WikidataResolver(cache=mock_cache)
        result = await resolver.resolve("XYZ Unknown Team")
        
        assert result is None

@pytest.mark.asyncio
async def test_extracts_wikipedia_urls(mock_cache):
    """Test that Wikipedia URLs for different languages are extracted correctly."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.side_effect = [
            create_mock_response(MOCK_SEARCH_RESPONSE_PEUGEOT),
            create_mock_response(MOCK_ENTITY_RESPONSE_PEUGEOT)
        ]
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        resolver = WikidataResolver(cache=mock_cache)
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
    
    with patch("httpx.AsyncClient") as mock_client:
        result = await resolver.resolve("Cached Team")
        
        assert result is not None
        assert result.qid == "Q12345"
        assert result.label == "Cached Team"
        
        # Verify cache was checked
        mock_cache.get.assert_called_once()
        # Verify HTTP client was NOT used
        mock_client.return_value.__aenter__.return_value.get.assert_not_called()

@pytest.mark.asyncio
async def test_writes_to_cache(mock_cache):
    """Test that successful API results are written to cache."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.side_effect = [
            create_mock_response(MOCK_SEARCH_RESPONSE_PEUGEOT),
            create_mock_response(MOCK_ENTITY_RESPONSE_PEUGEOT)
        ]
        mock_client.return_value.__aenter__.return_value.get = mock_get
        
        resolver = WikidataResolver(cache=mock_cache)
        await resolver.resolve("Peugeot cycling team")
        
        mock_cache.set.assert_called_once()
        args, kwargs = mock_cache.set.call_args
        assert "wikidata_api" in args[0]  # key
        assert "Q20658729" in args[1]  # content
        assert kwargs.get("domain") == "wikidata"
