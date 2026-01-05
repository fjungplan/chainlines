"""Tier mapping utility for professional cycling.

Maps source-specific tier labels to universal tier_level (1, 2, 3).

CyclingFlash uses these conventions:
- 2020-present: UCI WorldTeam, UCI ProTeam, UCI Continental Team
- 2011-2019: UCI WorldTeam, UCI Professional Continental Team, UCI Continental Team
- 2005-2010: UCI ProTeam, UCI Professional Continental Team, UCI Continental Team
- 1999-2004: Trade Team 1, Trade Team 2, Trade Team 3
- 1991-1998: Trade Team 1, Trade Team 2
- pre-1991: Trade Team 1

Our universal mapping:
| Date Range | Tier 1 | Tier 2 | Tier 3 |
|------------|--------|--------|--------|
| 1990–1995 | Professional | N/A | N/A |
| 1996–2004 | Trade Team I (GS1) | Trade Team II (GS2) | Trade Team III (GS3) |
| 2005–2014 | UCI ProTeam | Pro Continental | Continental |
| 2015–2019 | UCI WorldTeam | Pro Continental | Continental |
| 2020–Present | UCI WorldTeam | UCI ProTeam | Continental |
"""
from typing import Optional


def map_tier_label_to_level(label: Optional[str], year: int) -> Optional[int]:
    """
    Map a source-specific tier label to a universal tier_level (1, 2, 3).
    
    Args:
        label: Raw tier label from scraper (e.g., "UCI WorldTeam")
        year: Season year (determines which naming convention applies)
        
    Returns:
        1, 2, or 3 for the tier level, or None if not recognized
    """
    if not label:
        return None
        
    label = label.lower().strip()
    
    # Quick returns for numeric or shorthand inputs
    if label in ("1", "tier1"):
        return 1
    if label in ("2", "tier2"):
        return 2
    if label in ("3", "tier3"):
        return 3
    
    # ---------------------------------------------------------
    # CyclingFlash-specific mappings by era
    # ---------------------------------------------------------
    
    if year >= 2020:
        # 2020-present: UCI WorldTeam (T1), UCI ProTeam (T2), UCI Continental Team (T3)
        if "worldteam" in label or "world team" in label:
            return 1
        if "proteam" in label or "pro team" in label:
            return 2
        if "continental" in label:
            return 3
            
    elif year >= 2011:
        # 2011-2019: UCI WorldTeam (T1), UCI Professional Continental Team (T2), UCI Continental Team (T3)
        if "worldteam" in label or "world team" in label:
            return 1
        if "professional continental" in label or "pro continental" in label:
            return 2
        if "continental" in label:
            return 3
            
    elif year >= 2005:
        # 2005-2010: UCI ProTeam (T1), UCI Professional Continental Team (T2), UCI Continental Team (T3)
        if "proteam" in label or "pro team" in label:
            # In this era, ProTeam is Tier 1!
            return 1
        if "professional continental" in label or "pro continental" in label:
            return 2
        if "continental" in label:
            return 3
            
    elif year >= 1999:
        # 1999-2004: Trade Team 1 (T1), Trade Team 2 (T2), Trade Team 3 (T3)
        # Also GS1/GS2/GS3 in some sources
        if "trade team 1" in label or "tt1" in label or "gs1" in label:
            return 1
        if "trade team 2" in label or "tt2" in label or "gs2" in label:
            return 2
        if "trade team 3" in label or "tt3" in label or "gs3" in label:
            return 3
        # Handle roman numerals
        if "trade team i" in label and "ii" not in label and "iii" not in label:
            return 1
        if "trade team ii" in label and "iii" not in label:
            return 2
        if "trade team iii" in label:
            return 3
            
    elif year >= 1991:
        # 1991-1998: Trade Team 1 (T1), Trade Team 2 (T2) - only 2 tiers
        if "trade team 1" in label or "tt1" in label or "gs1" in label:
            return 1
        if "trade team 2" in label or "tt2" in label or "gs2" in label:
            return 2
        # Handle roman numerals
        if "trade team i" in label and "ii" not in label:
            return 1
        if "trade team ii" in label:
            return 2
            
    else:
        # pre-1991: Trade Team 1 only (single tier)
        if "trade team" in label or "tt1" in label or "professional" in label:
            return 1
    
    # ---------------------------------------------------------
    # Fallback generic patterns (source-agnostic)
    # ---------------------------------------------------------
    
    # WorldTour / WorldTeam variants
    if "worldtour" in label or "world tour" in label:
        return 1
    if "worldteam" in label or "world team" in label:
        return 1
        
    # Continental detection (must come before pro team checks)
    if "professional continental" in label or "pro continental" in label:
        return 2
    if "continental" in label:
        return 3
        
    # ProTeam detection (year-dependent, but fallback assumes modern)
    if "proteam" in label or "pro team" in label:
        return 2 if year >= 2020 else 1
    
    # Abbreviations
    if "wt" in label:
        return 1
    if "pt" in label:
        return 2 if year >= 2020 else 1
    if "ct" in label:
        return 3
    
    return None
