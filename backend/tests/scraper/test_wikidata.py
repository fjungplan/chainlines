import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.scraper.services.wikidata import WikidataResolver, WikidataResult

# Mock response for a known team (Peugeot)
MOCK_SPARQL_RESPONSE_PEUGEOT = {
    "results": {
        "bindings": [
            {
                "item": {"value": "http://www.wikidata.org/entity/Q20658729"},
                "itemLabel": {"value": "Peugeot cycling team"},
                "sitelink": {"value": "https://en.wikipedia.org/wiki/Peugeot_(cycling_team)"}
            },
            {
                "item": {"value": "http://www.wikidata.org/entity/Q20658729"},
                "itemLabel": {"value": "Peugeot cycling team"},
                "sitelink": {"value": "https://fr.wikipedia.org/wiki/Équipe_cycliste_Peugeot"}
            },
            {
                 "item": {"value": "http://www.wikidata.org/entity/Q20658729"},
                 "itemLabel": {"value": "Peugeot cycling team"},
                 "sitelink": {"value": "https://nl.wikipedia.org/wiki/Peugeot_(wielerploeg)"}
            }
        ]
    }
}

# Mock response for unknown team
MOCK_SPARQL_RESPONSE_EMPTY = {
    "results": {
        "bindings": []
    }
}

@pytest.fixture
def mock_cache():
    # CacheManager methods are synchronous
    mock = Mock()
    mock.get.return_value = None
    return mock

@pytest.mark.asyncio
async def test_resolve_known_team(mock_cache):
    """Test that a known team returns a valid WikidataResult."""
    with patch("httpx.AsyncClient") as mock_client:
        # The response object should be synchronous (json(), raise_for_status())
        mock_response = Mock()
        mock_response.json.return_value = MOCK_SPARQL_RESPONSE_PEUGEOT
        mock_response.raise_for_status = Mock()
        
        # client.get is async, so it returns a coroutine that resolves to mock_response
        # AsyncMock handles this if we set return_value
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        resolver = WikidataResolver(cache=mock_cache)
        result = await resolver.resolve("Peugeot cycling team")
        
        assert result is not None
        assert isinstance(result, WikidataResult)
        assert result.qid == "Q20658729"
        assert result.label == "Peugeot cycling team"
        assert "en" in result.sitelinks
        assert result.sitelinks["en"] == "https://en.wikipedia.org/wiki/Peugeot_(cycling_team)"

@pytest.mark.asyncio
async def test_resolve_unknown_team(mock_cache):
    """Test that an unknown team returns None."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = MOCK_SPARQL_RESPONSE_EMPTY
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        resolver = WikidataResolver(cache=mock_cache)
        result = await resolver.resolve("XYZ Unknown Team")
        
        assert result is None

@pytest.mark.asyncio
async def test_extracts_wikipedia_urls(mock_cache):
    """Test that Wikipedia URLs for different languages are extracted correctly."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = MOCK_SPARQL_RESPONSE_PEUGEOT
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        resolver = WikidataResolver(cache=mock_cache)
        result = await resolver.resolve("Peugeot cycling team")
        
        assert result is not None
        assert len(result.sitelinks) >= 3
        assert result.sitelinks["en"] == "https://en.wikipedia.org/wiki/Peugeot_(cycling_team)"
        assert result.sitelinks["fr"] == "https://fr.wikipedia.org/wiki/Équipe_cycliste_Peugeot"
        assert result.sitelinks["nl"] == "https://nl.wikipedia.org/wiki/Peugeot_(wielerploeg)"

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
        mock_response = Mock()
        mock_response.json.return_value = MOCK_SPARQL_RESPONSE_PEUGEOT
        mock_response.raise_for_status = Mock()
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        resolver = WikidataResolver(cache=mock_cache)
        await resolver.resolve("Peugeot cycling team")
        
        mock_cache.set.assert_called_once()
        args, kwargs = mock_cache.set.call_args
        assert args[0].startswith("wikidata:peugeot") # key
        assert "Q20658729" in args[1] # content
        assert kwargs.get("domain") == "wikidata"
