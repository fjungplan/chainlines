"""Tests for scraper utility functions."""
import pytest
from app.scraper.utils.country_mapper import map_country_to_code
from app.scraper.utils.sponsor_extractor import extract_title_sponsors

def test_map_country_to_code_basic():
    """Should map common country names to IOC codes."""
    assert map_country_to_code("Belgium") == "BEL"
    assert map_country_to_code("Netherlands") == "NED"
    assert map_country_to_code("France") == "FRA"
    assert map_country_to_code("Spain") == "ESP"
    assert map_country_to_code("Italy") == "ITA"

def test_map_country_to_code_variants():
    """Should handle ISO codes and case variations."""
    # ISO-2
    assert map_country_to_code("be") == "BEL"
    assert map_country_to_code("BE") == "BEL"
    
    # ISO-3
    assert map_country_to_code("bel") == "BEL"
    assert map_country_to_code("BEL") == "BEL"
    
    # Aliases
    assert map_country_to_code("Holland") == "NED"
    assert map_country_to_code("Great Britain") == "GBR"
    assert map_country_to_code("USA") == "USA"

def test_map_country_to_code_unknown():
    """Should return uppercase for unknown codes."""
    assert map_country_to_code("XYZ") == "XYZ"
    assert map_country_to_code(None) is None

def test_extract_title_sponsors_hyphen():
    """Should extract sponsors separated by hyphens."""
    assert extract_title_sponsors("Alpecin-Premier Tech") == ["Alpecin", "Premier Tech"]
    assert extract_title_sponsors("BORA - hansgrohe") == ["BORA", "hansgrohe"]

def test_extract_title_sponsors_ampersand():
    """Should extract sponsors separated by ampersand."""
    assert extract_title_sponsors("Arkéa - B&B Hotels") == ["Arkéa", "B&B Hotels"]
    assert extract_title_sponsors("Team Arkéa & B&B Hotels") == ["Arkéa", "B&B Hotels"] # Assuming regex handles spaces around &

def test_extract_title_sponsors_pipe():
    """Should extract sponsors separated by pipe."""
    assert extract_title_sponsors("Team Visma | Lease a Bike") == ["Visma", "Lease a Bike"]

def test_extract_title_sponsors_prefixes():
    """Should remove common team prefixes."""
    assert extract_title_sponsors("Team Jumbo-Visma") == ["Jumbo", "Visma"]
    assert extract_title_sponsors("Professional Cycling Team Example") == ["Example"]

def test_extract_title_sponsors_single():
    """Should handle single sponsor names."""
    assert extract_title_sponsors("Ineos Grenadiers") == ["Ineos Grenadiers"] # No delimiter
    assert extract_title_sponsors("UAE Team Emirates") == ["UAE Team Emirates"]
