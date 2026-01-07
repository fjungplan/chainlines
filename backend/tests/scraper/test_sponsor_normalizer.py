"""Tests for sponsor normalizer."""
import pytest
from app.scraper.utils.sponsor_normalizer import normalize_sponsor_name


def test_normalize_fdj():
    """FDJ should normalize to Française des Jeux."""
    name, parent = normalize_sponsor_name("FDJ")
    assert name == "Française des Jeux"
    

def test_normalize_fdj_united():
    """FDJ United should also normalize to Française des Jeux."""
    name, parent = normalize_sponsor_name("FDJ United")
    assert name == "Française des Jeux"


def test_normalize_lotto_belgian():
    """Lotto for Belgian teams should normalize to Nationale Loterij."""
    name, parent = normalize_sponsor_name("Lotto", "BEL")
    assert name == "Nationale Loterij"


def test_normalize_lotto_italian():
    """Lotto for Italian teams should normalize to Lotto Sport Italia."""
    name, parent = normalize_sponsor_name("Lotto", "ITA")
    assert name == "Lotto Sport Italia"


def test_normalize_lotto_no_country():
    """Lotto without country should stay as-is (ambiguous)."""
    name, parent = normalize_sponsor_name("Lotto")
    assert name == "Lotto"  # No normalization, country is needed


def test_normalize_dsm():
    """DSM should normalize to Royal DSM."""
    name, parent = normalize_sponsor_name("DSM")
    assert name == "Royal DSM"


def test_normalize_unknown():
    """Unknown brands should pass through unchanged."""
    name, parent = normalize_sponsor_name("Red Bull")
    assert name == "Red Bull"
    
    name, parent = normalize_sponsor_name("Alpecin")
    assert name == "Alpecin"
