"""Utility for extracting title sponsors from team names.

Team names in professional cycling typically contain the main sponsors,
separated by hyphens, dashes, or ampersands.

Examples:
- "Alpecin-Premier Tech" -> ["Alpecin", "Premier Tech"]
- "BORA - hansgrohe" -> ["BORA", "hansgrohe"]
- "Arkéa - B&B Hotels" -> ["Arkéa", "B&B Hotels"]
- "Team Visma | Lease a Bike" -> ["Visma", "Lease a Bike"]
- "UAE Team Emirates" -> ["UAE Team Emirates"]  # No split, single sponsor
"""

import re
from typing import List

# Common team prefixes to strip (not sponsors)
TEAM_PREFIXES = [
    "team", "cycling team", "professional cycling team",
    "pro cycling", "racing", "development team"
]

# Delimiters that separate sponsor names
DELIMITER_PATTERN = re.compile(r'\s*[-–—|/]\s*|\s+&\s+')


def extract_title_sponsors(team_name: str) -> List[str]:
    """Extract title sponsor names from a team name.
    
    Args:
        team_name: Full team name (e.g., "Alpecin-Premier Tech")
        
    Returns:
        List of sponsor names extracted from the team name
    """
    if not team_name:
        return []
    
    name = team_name.strip()
    
    # Remove common prefixes
    name_lower = name.lower()
    for prefix in TEAM_PREFIXES:
        if name_lower.startswith(prefix + " "):
            name = name[len(prefix) + 1:].strip()
            name_lower = name.lower()
    
    # Split by delimiters
    parts = DELIMITER_PATTERN.split(name)
    
    # Clean up each part
    sponsors = []
    for part in parts:
        cleaned = part.strip()
        if cleaned and len(cleaned) > 1:  # Ignore single-character fragments
            # Skip if it's just "Team" or similar
            if cleaned.lower() not in TEAM_PREFIXES:
                sponsors.append(cleaned)
    
    # If no split occurred, the whole name is the sponsor
    if not sponsors and name:
        sponsors = [name]
    
    return sponsors
