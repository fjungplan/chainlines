"""Sponsor name normalization utilities."""
from typing import Optional, Tuple

# Known abbreviations that should be normalized to their full names
# Format: (abbreviation, full_name, country_code_if_applicable)
KNOWN_ABBREVIATIONS = [
    # French lottery
    ("FDJ", "Française des Jeux", None),
    ("FDJ United", "Française des Jeux", None),
    
    # Belgian lottery (only for BEL teams)
    ("Lotto", "Nationale Loterij", "BEL"),
    
    # Italian sports brand (only for ITA teams)  
    ("Lotto", "Lotto Sport Italia", "ITA"),
    
    # Dutch multinational
    ("DSM", "Royal DSM", None),
    
    # Emirates
    ("UAE", "Emirates", None),
]


def normalize_sponsor_name(
    sponsor_name: str,
    country_code: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """
    Normalize known abbreviations to their full names.
    
    Args:
        sponsor_name: The sponsor name to normalize
        country_code: 3-letter country code for context (e.g., BEL, ITA)
    
    Returns:
        Tuple of (normalized_name, parent_company)
        - normalized_name: The full company name if abbreviation is known, otherwise original
        - parent_company: The parent company name if applicable
    
    Examples:
        >>> normalize_sponsor_name("FDJ")
        ("Française des Jeux", None)
        
        >>> normalize_sponsor_name("Lotto", "BEL")
        ("Nationale Loterij", None)
        
        >>> normalize_sponsor_name("Lotto", "ITA")
        ("Lotto Sport Italia", None)
        
        >>> normalize_sponsor_name("Red Bull")
        ("Red Bull", None)  # No change for unknown names
    """
    sponsor_lower = sponsor_name.lower()
    
    # Check for exact matches first (case-insensitive)
    for abbrev, full_name, required_country in KNOWN_ABBREVIATIONS:
        if sponsor_lower == abbrev.lower():
            # If no country required, return immediately
            if required_country is None:
                return (full_name, None)
            # If country matches, return
            if country_code and country_code.upper() == required_country:
                return (full_name, None)
    
    # No match found, return original
    return (sponsor_name, None)
