"""Tier mapping utility for professional cycling."""
from typing import Optional

def map_tier_label_to_level(label: Optional[str], year: int) -> Optional[int]:
    """
    Map a source-specific tier label to a universal tier_level (1, 2, 3).
    
    Tier Level 1: Highest professional level
    Tier Level 2: Second professional level
    Tier Level 3: Third level (Continental)
    
    Based on docs/final_schema_doc.md:
    1990–1995: Professional (Tier 1)
    1996–2004: GS1 (Tier 1), GS2 (Tier 2), GS3 (Tier 3)
    2005–2014: ProTeam (Tier 1), Pro Continental (Tier 2), Continental (Tier 3)
    2015–2019: WorldTeam (Tier 1), Pro Continental (Tier 2), Continental (Tier 3)
    2020–Pres: WorldTeam (Tier 1), ProTeam (Tier 2), Continental (Tier 3)
    """
    if not label:
        return None
        
    label = label.lower().strip()
    
    # Generic aliases used in CLI or normalized
    if label in ("wt", "tier1", "1", "worldteam", "worldtour"):
        return 1
    if label in ("pt", "tier2", "2", "proteam", "pro continental"):
        # Note: 'proteam' is Tier 1 pre-2015, but Tier 2 post-2020.
        # We'll refine this below based on year if needed.
        pass
    if label in ("ct", "tier3", "3", "continental"):
        return 3

    # Year-specific mapping
    if year >= 2020:
        if "worldteam" in label or "wt" in label: return 1
        if "proteam" in label or "pt" in label: return 2
        if "continental" in label or "ct" in label: return 3
    elif year >= 2015:
        if "worldteam" in label or "wt" in label: return 1
        if "pro continental" in label or "pt" in label: return 2
        if "continental" in label or "ct" in label: return 3
    elif year >= 2005:
        # 2005-2014: "ProTeam" was Tier 1
        if "proteam" in label or "wt" in label: return 1
        if "pro continental" in label or "pt" in label: return 2
        if "continental" in label or "ct" in label: return 3
    elif year >= 1996:
        if "gs1" in label or "trade team i" in label: return 1
        if "gs2" in label or "trade team ii" in label: return 2
        if "gs3" in label or "trade team iii" in label: return 3
    elif year >= 1990:
        if "professional" in label: return 1
        
    # Final fallbacks for common abbreviations if year logic didn't catch them
    if "wt" in label: return 1
    if "pt" in label or "pro continental" in label or "pro team" in label: return 2
    if "ct" in label or "continental" in label: return 3
    
    return None
