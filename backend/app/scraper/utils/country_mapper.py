
"""Utility for mapping country names and 2-letter codes to 3-letter UCI codes."""

COUNTRY_MAP = {
    "belgium": "BEL",
    "france": "FRA",
    "germany": "GER",
    "kazakhstan": "KAZ",
    "bahrain": "BRN",
    "denmark": "DEN",
    "spain": "ESP",
    "italy": "ITA",
    "netherlands": "NED",
    "norway": "NOR",
    "united states": "USA",
    "united kingdom": "GBR",
    "australia": "AUS",
    "austria": "AUT",
    "switzerland": "SUI",
    "colombia": "COL",
    "slovenia": "SLO",
    "poland": "POL",
    "portugal": "POR",
    "eritre": "ERI",
    "eritrea": "ERI",
    "new zealand": "NZL",
    "canada": "CAN",
    "south africa": "RSA",
    "ireland": "IRL",
    "luxembourg": "LUX",
    "czech republic": "CZE",
    "slovakia": "SVK",
    "russia": "RUS",
    "ukraine": "UKR",
    "belarus": "BLR",
    "estonia": "EST",
    "latvia": "LAT",
    "lithuania": "LTU",
    "hungary": "HUN",
    "romania": "ROU",
    "bulgaria": "BUL",
    "greece": "GRE",
    "turkey": "TUR",
    "israel": "ISR",
    "japan": "JPN",
    "china": "CHN",
    "south korea": "KOR",
    "united arab emirates": "UAE",
}

def map_country_to_code(value: str) -> str:
    """Map country name or 2-letter code to 3-letter UCI code.
    
    Returns original value if no mapping found.
    """
    if not value:
        return value
        
    val = value.strip().lower()
    
    # Direct name mapping
    if val in COUNTRY_MAP:
        return COUNTRY_MAP[val]
    
    # Handle common abbreviations/variants
    if val == "usa": return "USA"
    if val == "uae": return "UAE"
    if val == "gbr": return "GBR"
    
    return value.upper() # Fallback to upper case
