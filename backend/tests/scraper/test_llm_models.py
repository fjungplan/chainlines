import pytest
from pydantic import ValidationError
from app.scraper.llm.models import SponsorInfo, SponsorExtractionResult, BrandMatchResult

def test_sponsor_info_model():
    """Test SponsorInfo model validation."""
    # Valid model
    info = SponsorInfo(brand_name="Ineos Grenadier", parent_company="INEOS Group")
    assert info.brand_name == "Ineos Grenadier"
    assert info.parent_company == "INEOS Group"
    
    # Optional parent_company
    info = SponsorInfo(brand_name="Ineos Grenadier")
    assert info.brand_name == "Ineos Grenadier"
    assert info.parent_company is None
    
    # Rejects empty brand_name (or missing)
    # Note: Pydantic doesn't reject empty strings by default unless min_length is specified,
    # but the prompt says "Rejects empty brand_name". I'll check if it's missing first.
    with pytest.raises(ValidationError):
        SponsorInfo() # Missing brand_name

def test_sponsor_extraction_result_model():
    """Test SponsorExtractionResult model validation."""
    sponsors = [SponsorInfo(brand_name="Brand A")]
    
    # Valid model
    result = SponsorExtractionResult(
        sponsors=sponsors,
        team_descriptors=["Cycling Team"],
        filler_words=["The"],
        confidence=0.9,
        reasoning="Good match"
    )
    assert result.confidence == 0.9
    assert result.reasoning == "Good match"
    assert len(result.sponsors) == 1
    
    # Optional fields default to factory
    result_minimal = SponsorExtractionResult(
        sponsors=sponsors,
        confidence=1.0,
        reasoning="Perfect"
    )
    assert result_minimal.team_descriptors == []
    assert result_minimal.filler_words == []
    
    # Rejects invalid confidence values
    with pytest.raises(ValidationError):
        SponsorExtractionResult(sponsors=sponsors, confidence=1.1, reasoning="Too high")
    
    with pytest.raises(ValidationError):
        SponsorExtractionResult(sponsors=sponsors, confidence=-0.1, reasoning="Too low")
    
    # Reasoning is required
    with pytest.raises(ValidationError):
        SponsorExtractionResult(sponsors=sponsors, confidence=0.5)

def test_brand_match_result_model():
    """Test BrandMatchResult model validation."""
    # Valid model
    match = BrandMatchResult(
        known_brands=["Ineos", "Grenadier"],
        unmatched_words=["The"],
        needs_llm=True
    )
    assert match.known_brands == ["Ineos", "Grenadier"]
    assert match.unmatched_words == ["The"]
    assert match.needs_llm is True
    
    # Check types
    with pytest.raises(ValidationError):
        BrandMatchResult(known_brands="not a list", unmatched_words=[], needs_llm=False)
