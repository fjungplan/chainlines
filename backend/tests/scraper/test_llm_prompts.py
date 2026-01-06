"""Test LLM prompts for data extraction."""
import pytest
from pydantic import ValidationError
from unittest.mock import AsyncMock, patch
from app.scraper.llm.models import SponsorInfo


def test_scraped_team_data_validates():
    """ScrapedTeamData should validate correctly."""
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    data = ScrapedTeamData(
        name="Team Visma",
        season_year=2024,
        sponsors=[
            SponsorInfo(brand_name="Visma"),
            SponsorInfo(brand_name="Lease a Bike")
        ]
    )
    assert data.name == "Team Visma"
    assert len(data.sponsors) == 2
    assert data.sponsors[0].brand_name == "Visma"


def test_scraped_team_data_requires_name():
    """ScrapedTeamData should require name field."""
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    with pytest.raises(ValidationError):
        ScrapedTeamData(season_year=2024)


@pytest.mark.asyncio
async def test_extract_team_data_prompt():
    """LLMService.extract_team_data should return structured data."""
    from app.scraper.llm.prompts import ScraperPrompts
    from app.scraper.sources.cyclingflash import ScrapedTeamData
    
    mock_service = AsyncMock()
    mock_service.generate_structured = AsyncMock(
        return_value=ScrapedTeamData(
            name="UAE Team Emirates",
            uci_code="UAD",
            tier="WorldTour",
            country_code="UAE",
            sponsors=[
                SponsorInfo(brand_name="Emirates"),
                SponsorInfo(brand_name="Colnago")
            ],
            season_year=2024
        )
    )
    
    prompts = ScraperPrompts(llm_service=mock_service)
    
    result = await prompts.extract_team_data(
        html="<html>...</html>",
        season_year=2024
    )
    
    assert result.name == "UAE Team Emirates"
    assert result.uci_code == "UAD"
    mock_service.generate_structured.assert_called_once()

