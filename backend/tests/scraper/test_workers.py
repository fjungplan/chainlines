import pytest
from pydantic import ValidationError
from app.scraper.orchestration.workers import SourceWorker, SourceData, WikipediaWorker, CyclingRankingWorker
from unittest.mock import AsyncMock, MagicMock


def test_source_data_model_validates():
    """SourceData model accepts valid data."""
    data = SourceData(
        source="test",
        raw_content="<html></html>",
        founded_year=1990,
        dissolved_year=2000,
        history_text="Some history.",
        extra={"meta": "data"}
    )
    assert data.source == "test"
    assert data.founded_year == 1990
    assert data.extra["meta"] == "data"

def test_source_worker_is_abstract():
    """Cannot instantiate SourceWorker directly."""
    with pytest.raises(TypeError):
        SourceWorker()

@pytest.fixture
def mock_scraper():
    scraper = MagicMock()
    scraper.fetch = AsyncMock()
    return scraper

@pytest.mark.asyncio
async def test_wikipedia_worker_extracts_history(mock_scraper):
    """Worker extracts text between History header and next header."""
    html = """
        <html>
        <body>
            <h1>Team Name</h1>
            <h2 id="History">History</h2>
            <p>The team was founded in 1990.</p>
            <p>It won many races.</p>
            <h2>2020 Season</h2>
            <p>This should not be included.</p>
        </body>
    </html>
    """
    mock_scraper.fetch.return_value = html
    
    worker = WikipediaWorker(mock_scraper)
    result = await worker.fetch("http://wiki.com/Team")
    
    assert result.source == "wikipedia"
    assert "The team was founded in 1990." in result.history_text
    assert "It won many races." in result.history_text
    assert "This should not be included" not in result.history_text

@pytest.mark.asyncio
async def test_wikipedia_worker_handles_no_history(mock_scraper):
    """Worker returns None for history_text if no History section found."""
    html = """
    <html>
        <body>
            <h1>Team Name</h1>
            <p>No history section here.</p>
        </body>
    </html>
    """
    mock_scraper.fetch.return_value = html
    
    worker = WikipediaWorker(mock_scraper)
    result = await worker.fetch("http://wiki.com/Team")
    
    assert result.history_text is None

@pytest.mark.asyncio
async def test_wikipedia_worker_extracts_founded_year(mock_scraper):
    """Worker extracts founded year from infobox."""
    html = """
    <html>
        <body>
            <table class="infobox">
                <tr>
                    <th>Founded</th>
                    <td>1995; 29 years ago</td>
                </tr>
            </table>
            <h2>History</h2>
            <p>Content.</p>
        </body>
    </html>
    """
    mock_scraper.fetch.return_value = html
    
    worker = WikipediaWorker(mock_scraper)
    result = await worker.fetch("http://wiki.com/Team")
    
    assert result.founded_year == 1995

@pytest.mark.asyncio
async def test_cycling_ranking_worker_extracts_years(mock_scraper):
    """Worker extracts founded and dissolved years from page."""
    html = """
    <html>
        <body>
            <div class="main">
                <h1>Team Name</h1>
                <dl>
                   <dt>Founded</dt>
                   <dd class="founded">1998</dd>
                   <dt>Dissolved</dt>
                   <dd class="dissolved">2010</dd>
                </dl>
            </div>
        </body>
    </html>
    """
    mock_scraper.fetch.return_value = html
    
    worker = CyclingRankingWorker(mock_scraper)
    result = await worker.fetch("http://cyclingranking.com/team/123")
    
    assert result.source == "cyclingranking"
    assert result.founded_year == 1998
    assert result.dissolved_year == 2010

@pytest.mark.asyncio
async def test_cycling_ranking_worker_handles_active_team(mock_scraper):
    """Worker handles active teams (no dissolved year)."""
    html = """
    <html>
        <body>
             <div class="main">
                <h1>Team Name</h1>
                <dl>
                   <dt>Founded</dt>
                   <dd class="founded">2005</dd>
                </dl>
            </div>
        </body>
    </html>
    """
    mock_scraper.fetch.return_value = html
    
    worker = CyclingRankingWorker(mock_scraper)
    result = await worker.fetch("http://cyclingranking.com/team/456")
    
    assert result.founded_year == 2005
    assert result.dissolved_year is None
