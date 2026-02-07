import pytest
from app.api.admin.optimizer import _get_family_name

def test_family_naming_heuristics():
    # Longest duration wins
    nodes = [
        {"name": "Short Team", "founding_year": 2020, "dissolution_year": 2021}, # 1 year
        {"name": "Long Team", "founding_year": 2010, "dissolution_year": 2020},  # 10 years
        {"name": "Medium Team", "founding_year": 2015, "dissolution_year": 2019} # 4 years
    ]
    assert _get_family_name(nodes) == "Long Team"

    # Tie-break: More eras win
    nodes_eras = [
        {"name": "No Eras", "founding_year": 2010, "dissolution_year": 2020, "eras": []},
        {"name": "Many Eras", "founding_year": 2010, "dissolution_year": 2020, "eras": [{}, {}, {}]}
    ]
    assert _get_family_name(nodes_eras) == "Many Eras"

    # Tie-break: Younger founding year (founded later) wins if durations equal
    nodes_younger = [
        {"name": "Old Founding", "founding_year": 1990, "dissolution_year": 2000},
        {"name": "Young Founding", "founding_year": 2010, "dissolution_year": 2020}
    ]
    assert _get_family_name(nodes_younger) == "Young Founding"

def test_family_naming_empty():
    assert _get_family_name([]) == "Unknown Family"
    assert _get_family_name([{"name": None}]) == "Unknown Family"
    assert _get_family_name([{"name": "Found"}]) == "Found"
def test_family_naming_zombie_nodes():
    # Ancient zombie team (1980-1985, no dissolution)
    # Modern active team (2000-2025, no dissolution)
    nodes = [
        {
            "name": "Ancient Zombie", 
            "founding_year": 1980, 
            "dissolution_year": None,
            "eras": [{"year": 1980}, {"year": 1985}]
        },
        {
            "name": "Active Powerhouse", 
            "founding_year": 2000, 
            "dissolution_year": None,
            "eras": [{"year": 2000}, {"year": 2025}]
        }
    ]
    # Current (incorrect) behavior would choose Ancient Zombie (1980-2026 vs 2000-2026)
    # Expected behavior should choose Active Powerhouse (2000-2025 vs 1980-1985)
    assert _get_family_name(nodes) == "Active Powerhouse"
