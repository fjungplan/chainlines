"""Tests for sponsor extraction LLM prompt."""
import pytest
from unittest.mock import AsyncMock
from app.scraper.llm.prompts import ScraperPrompts
from app.scraper.llm.models import SponsorExtractionResult, SponsorInfo


@pytest.mark.asyncio
async def test_extract_sponsors_from_name():
    """Test sponsor extraction prompt formatting and call."""
    mock_llm = AsyncMock()
    mock_llm.generate_structured = AsyncMock(
        return_value=SponsorExtractionResult(
            sponsors=[SponsorInfo(brand_name="Bahrain")],
            team_descriptors=["Victorious"],
            filler_words=[],
            confidence=0.95,
            reasoning="Bahrain is the sponsor, Victorious is a descriptor"
        )
    )
    
    prompts = ScraperPrompts(llm_service=mock_llm)
    
    result = await prompts.extract_sponsors_from_name(
        team_name="Bahrain Victorious",
        season_year=2024,
        country_code="BHR",
        partial_matches=[]
    )
    
    assert len(result.sponsors) == 1
    assert result.sponsors[0].brand_name == "Bahrain"
    assert "Victorious" in result.team_descriptors
    assert result.confidence == 0.95
    
    # Verify LLM was called with formatted prompt
    mock_llm.generate_structured.assert_called_once()
    call_args = mock_llm.generate_structured.call_args
    assert "Bahrain Victorious" in call_args.kwargs["prompt"]
    assert "2024" in call_args.kwargs["prompt"]
    assert call_args.kwargs["response_model"] == SponsorExtractionResult


@pytest.mark.asyncio
async def test_extract_sponsors_with_partial_matches():
    """Test prompt includes partial matches from DB."""
    mock_llm = AsyncMock()
    mock_llm.generate_structured = AsyncMock(
        return_value=SponsorExtractionResult(
            sponsors=[
                SponsorInfo(brand_name="Lotto NL"),
                SponsorInfo(brand_name="Jumbo")
            ],
            team_descriptors=[],
            filler_words=["Team"],
            confidence=0.90,
            reasoning="Lotto NL and Jumbo are both sponsors"
        )
    )
    
    prompts = ScraperPrompts(llm_service=mock_llm)
    await prompts.extract_sponsors_from_name(
        team_name="Lotto NL Jumbo Team",
        season_year=2016,
        country_code="NED",
        partial_matches=["Lotto", "Jumbo"]
    )
    
    call_args = mock_llm.generate_structured.call_args
    prompt = call_args.kwargs["prompt"]
    # Partial matches should appear in the prompt
    assert "Lotto" in prompt
    assert "Jumbo" in prompt


@pytest.mark.asyncio
async def test_extract_sponsors_with_parent_company():
    """Test extraction includes parent company when known."""
    mock_llm = AsyncMock()
    mock_llm.generate_structured = AsyncMock(
        return_value=SponsorExtractionResult(
            sponsors=[
                SponsorInfo(brand_name="Ineos Grenadier", parent_company="INEOS Group")
            ],
            team_descriptors=["s"],
            filler_words=[],
            confidence=0.92,
            reasoning="Ineos Grenadier is the brand, INEOS Group is the parent company"
        )
    )
    
    prompts = ScraperPrompts(llm_service=mock_llm)
    result = await prompts.extract_sponsors_from_name(
        team_name="Ineos Grenadiers",
        season_year=2024,
        country_code="GBR",
        partial_matches=[]
    )
    
    assert result.sponsors[0].parent_company == "INEOS Group"


@pytest.mark.asyncio
async def test_extract_sponsors_unknown_country():
    """Test extraction handles unknown country code."""
    mock_llm = AsyncMock()
    mock_llm.generate_structured = AsyncMock(
        return_value=SponsorExtractionResult(
            sponsors=[SponsorInfo(brand_name="Test Sponsor")],
            team_descriptors=[],
            filler_words=["Cycling", "Team"],
            confidence=0.88,
            reasoning="Test extraction"
        )
    )
    
    prompts = ScraperPrompts(llm_service=mock_llm)
    await prompts.extract_sponsors_from_name(
        team_name="Test Sponsor Cycling Team",
        season_year=2023,
        country_code=None,  # Unknown country
        partial_matches=[]
    )
    
    call_args = mock_llm.generate_structured.call_args
    prompt = call_args.kwargs["prompt"]
    # Should show "Unknown" for missing country
    assert "Unknown" in prompt


@pytest.mark.asyncio
async def test_extract_sponsors_multiple_sponsors():
    """Test extraction of multiple sponsors from team name."""
    mock_llm = AsyncMock()
    mock_llm.generate_structured = AsyncMock(
        return_value=SponsorExtractionResult(
            sponsors=[
                SponsorInfo(brand_name="UAE"),
                SponsorInfo(brand_name="Emirates"),
                SponsorInfo(brand_name="XRG")
            ],
            team_descriptors=["Team"],
            filler_words=[],
            confidence=0.95,
            reasoning="UAE, Emirates, and XRG are all sponsors"
        )
    )
    
    prompts = ScraperPrompts(llm_service=mock_llm)
    result = await prompts.extract_sponsors_from_name(
        team_name="UAE Team Emirates XRG",
        season_year=2024,
        country_code="UAE",
        partial_matches=["UAE", "Emirates"]
    )
    
    assert len(result.sponsors) == 3
    sponsor_names = [s.brand_name for s in result.sponsors]
    assert "UAE" in sponsor_names
    assert "Emirates" in sponsor_names
    assert "XRG" in sponsor_names
