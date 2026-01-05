"""Utility for mapping country names and ISO codes to 3-letter IOC/UCI codes.

Covers all 206 IOC member countries plus common territories used in cycling.
Supports mapping from:
- Full English country names (case-insensitive)
- 2-letter ISO 3166-1 alpha-2 codes
- 3-letter ISO 3166-1 alpha-3 codes

Output: 3-letter IOC code (used by UCI for cycling registrations)
"""

from typing import Optional

# Comprehensive mapping: (English Name, ISO-2, ISO-3) -> IOC Code
# Format: "lookup_key": "IOC_CODE"
# All lookup keys are lowercase for case-insensitive matching

COUNTRY_DATA = {
    # A
    "afghanistan": "AFG", "af": "AFG", "afg": "AFG",
    "albania": "ALB", "al": "ALB", "alb": "ALB",
    "algeria": "ALG", "dz": "ALG", "dza": "ALG",
    "american samoa": "ASA", "as": "ASA", "asm": "ASA",
    "andorra": "AND", "ad": "AND", "and": "AND",
    "angola": "ANG", "ao": "ANG", "ago": "ANG",
    "antigua and barbuda": "ANT", "ag": "ANT", "atg": "ANT",
    "argentina": "ARG", "ar": "ARG", "arg": "ARG",
    "armenia": "ARM", "am": "ARM", "arm": "ARM",
    "aruba": "ARU", "aw": "ARU", "abw": "ARU",
    "australia": "AUS", "au": "AUS", "aus": "AUS",
    "austria": "AUT", "at": "AUT", "aut": "AUT",
    "azerbaijan": "AZE", "az": "AZE", "aze": "AZE",
    
    # B
    "bahamas": "BAH", "bs": "BAH", "bhs": "BAH",
    "bahrain": "BRN", "bh": "BRN", "bhr": "BRN",
    "bangladesh": "BAN", "bd": "BAN", "bgd": "BAN",
    "barbados": "BAR", "bb": "BAR", "brb": "BAR",
    "belarus": "BLR", "by": "BLR", "blr": "BLR",
    "belgium": "BEL", "be": "BEL", "bel": "BEL",
    "belize": "BIZ", "bz": "BIZ", "blz": "BIZ",
    "benin": "BEN", "bj": "BEN", "ben": "BEN",
    "bermuda": "BER", "bm": "BER", "bmu": "BER",
    "bhutan": "BHU", "bt": "BHU", "btn": "BHU",
    "bolivia": "BOL", "bo": "BOL", "bol": "BOL",
    "bosnia and herzegovina": "BIH", "ba": "BIH", "bih": "BIH",
    "botswana": "BOT", "bw": "BOT", "bwa": "BOT",
    "brazil": "BRA", "br": "BRA", "bra": "BRA",
    "british virgin islands": "IVB", "vg": "IVB", "vgb": "IVB",
    "brunei": "BRU", "bn": "BRU", "brn_brunei": "BRU",
    "bulgaria": "BUL", "bg": "BUL", "bgr": "BUL",
    "burkina faso": "BUR", "bf": "BUR", "bfa": "BUR",
    "burundi": "BDI", "bi": "BDI", "bdi": "BDI",
    
    # C
    "cambodia": "CAM", "kh": "CAM", "khm": "CAM",
    "cameroon": "CMR", "cm": "CMR", "cmr": "CMR",
    "canada": "CAN", "ca": "CAN", "can": "CAN",
    "cape verde": "CPV", "cv": "CPV", "cpv": "CPV",
    "cayman islands": "CAY", "ky": "CAY", "cym": "CAY",
    "central african republic": "CAF", "cf": "CAF", "caf": "CAF",
    "chad": "CHA", "td": "CHA", "tcd": "CHA",
    "chile": "CHI", "cl": "CHI", "chl": "CHI",
    "china": "CHN", "cn": "CHN", "chn": "CHN",
    "chinese taipei": "TPE", "tw": "TPE", "twn": "TPE",
    "taiwan": "TPE",
    "colombia": "COL", "co": "COL", "col": "COL",
    "comoros": "COM", "km": "COM", "com": "COM",
    "congo": "CGO", "cg": "CGO", "cog": "CGO",
    "republic of the congo": "CGO",
    "dr congo": "COD", "cd": "COD", "cod": "COD",
    "democratic republic of the congo": "COD",
    "cook islands": "COK", "ck": "COK", "cok": "COK",
    "costa rica": "CRC", "cr": "CRC", "cri": "CRC",
    "croatia": "CRO", "hr": "CRO", "hrv": "CRO",
    "cuba": "CUB", "cu": "CUB", "cub": "CUB",
    "cyprus": "CYP", "cy": "CYP", "cyp": "CYP",
    "czech republic": "CZE", "cz": "CZE", "cze": "CZE",
    "czechia": "CZE",
    
    # D
    "denmark": "DEN", "dk": "DEN", "dnk": "DEN",
    "djibouti": "DJI", "dj": "DJI", "dji": "DJI",
    "dominica": "DMA", "dm": "DMA", "dma": "DMA",
    "dominican republic": "DOM", "do": "DOM", "dom": "DOM",
    
    # E
    "ecuador": "ECU", "ec": "ECU", "ecu": "ECU",
    "egypt": "EGY", "eg": "EGY", "egy": "EGY",
    "el salvador": "ESA", "sv": "ESA", "slv": "ESA",
    "equatorial guinea": "GEQ", "gq": "GEQ", "gnq": "GEQ",
    "eritrea": "ERI", "er": "ERI", "eri": "ERI",
    "estonia": "EST", "ee": "EST", "est": "EST",
    "eswatini": "SWZ", "sz": "SWZ", "swz": "SWZ",
    "swaziland": "SWZ",
    "ethiopia": "ETH", "et": "ETH", "eth": "ETH",
    
    # F
    "fiji": "FIJ", "fj": "FIJ", "fji": "FIJ",
    "finland": "FIN", "fi": "FIN", "fin": "FIN",
    "france": "FRA", "fr": "FRA", "fra": "FRA",
    
    # G
    "gabon": "GAB", "ga": "GAB", "gab": "GAB",
    "gambia": "GAM", "gm": "GAM", "gmb": "GAM",
    "georgia": "GEO", "ge": "GEO", "geo": "GEO",
    "germany": "GER", "de": "GER", "deu": "GER",
    "ghana": "GHA", "gh": "GHA", "gha": "GHA",
    "great britain": "GBR", "gb": "GBR", "gbr": "GBR",
    "united kingdom": "GBR", "uk": "GBR",
    "greece": "GRE", "gr": "GRE", "grc": "GRE",
    "grenada": "GRN", "gd": "GRN", "grd": "GRN",
    "guam": "GUM", "gu": "GUM", "gum": "GUM",
    "guatemala": "GUA", "gt": "GUA", "gtm": "GUA",
    "guinea": "GUI", "gn": "GUI", "gin": "GUI",
    "guinea-bissau": "GBS", "gw": "GBS", "gnb": "GBS",
    "guyana": "GUY", "gy": "GUY", "guy": "GUY",
    
    # H
    "haiti": "HAI", "ht": "HAI", "hti": "HAI",
    "honduras": "HON", "hn": "HON", "hnd": "HON",
    "hong kong": "HKG", "hk": "HKG", "hkg": "HKG",
    "hungary": "HUN", "hu": "HUN", "hun": "HUN",
    
    # I
    "iceland": "ISL", "is": "ISL", "isl": "ISL",
    "india": "IND", "in": "IND", "ind": "IND",
    "indonesia": "INA", "id": "INA", "idn": "INA",
    "iran": "IRI", "ir": "IRI", "irn": "IRI",
    "iraq": "IRQ", "iq": "IRQ", "irq": "IRQ",
    "ireland": "IRL", "ie": "IRL", "irl": "IRL",
    "israel": "ISR", "il": "ISR", "isr": "ISR",
    "italy": "ITA", "it": "ITA", "ita": "ITA",
    "ivory coast": "CIV", "ci": "CIV", "civ": "CIV",
    "cote d'ivoire": "CIV",
    
    # J
    "jamaica": "JAM", "jm": "JAM", "jam": "JAM",
    "japan": "JPN", "jp": "JPN", "jpn": "JPN",
    "jordan": "JOR", "jo": "JOR", "jor": "JOR",
    
    # K
    "kazakhstan": "KAZ", "kz": "KAZ", "kaz": "KAZ",
    "kenya": "KEN", "ke": "KEN", "ken": "KEN",
    "kiribati": "KIR", "ki": "KIR", "kir": "KIR",
    "korea": "KOR", "kr": "KOR", "kor": "KOR",
    "south korea": "KOR",
    "north korea": "PRK", "kp": "PRK", "prk": "PRK",
    "kosovo": "KOS", "xk": "KOS",
    "kuwait": "KUW", "kw": "KUW", "kwt": "KUW",
    "kyrgyzstan": "KGZ", "kg": "KGZ", "kgz": "KGZ",
    
    # L
    "laos": "LAO", "la": "LAO", "lao": "LAO",
    "latvia": "LAT", "lv": "LAT", "lva": "LAT",
    "lebanon": "LBN", "lb": "LBN", "lbn": "LBN",
    "lesotho": "LES", "ls": "LES", "lso": "LES",
    "liberia": "LBR", "lr": "LBR", "lbr": "LBR",
    "libya": "LBA", "ly": "LBA", "lby": "LBA",
    "liechtenstein": "LIE", "li": "LIE", "lie": "LIE",
    "lithuania": "LTU", "lt": "LTU", "ltu": "LTU",
    "luxembourg": "LUX", "lu": "LUX", "lux": "LUX",
    
    # M
    "madagascar": "MAD", "mg": "MAD", "mdg": "MAD",
    "malawi": "MAW", "mw": "MAW", "mwi": "MAW",
    "malaysia": "MAS", "my": "MAS", "mys": "MAS",
    "maldives": "MDV", "mv": "MDV", "mdv": "MDV",
    "mali": "MLI", "ml": "MLI", "mli": "MLI",
    "malta": "MLT", "mt": "MLT", "mlt": "MLT",
    "marshall islands": "MHL", "mh": "MHL", "mhl": "MHL",
    "mauritania": "MTN", "mr": "MTN", "mrt": "MTN",
    "mauritius": "MRI", "mu": "MRI", "mus": "MRI",
    "mexico": "MEX", "mx": "MEX", "mex": "MEX",
    "micronesia": "FSM", "fm": "FSM", "fsm": "FSM",
    "moldova": "MDA", "md": "MDA", "mda": "MDA",
    "monaco": "MON", "mc": "MON", "mco": "MON",
    "mongolia": "MGL", "mn": "MGL", "mng": "MGL",
    "montenegro": "MNE", "me": "MNE", "mne": "MNE",
    "morocco": "MAR", "ma": "MAR", "mar": "MAR",
    "mozambique": "MOZ", "mz": "MOZ", "moz": "MOZ",
    "myanmar": "MYA", "mm": "MYA", "mmr": "MYA",
    "burma": "MYA",
    
    # N
    "namibia": "NAM", "na": "NAM", "nam": "NAM",
    "nauru": "NRU", "nr": "NRU", "nru": "NRU",
    "nepal": "NEP", "np": "NEP", "npl": "NEP",
    "netherlands": "NED", "nl": "NED", "nld": "NED",
    "holland": "NED",
    "new zealand": "NZL", "nz": "NZL", "nzl": "NZL",
    "nicaragua": "NCA", "ni": "NCA", "nic": "NCA",
    "niger": "NIG", "ne": "NIG", "ner": "NIG",
    "nigeria": "NGR", "ng": "NGR", "nga": "NGR",
    "north macedonia": "MKD", "mk": "MKD", "mkd": "MKD",
    "macedonia": "MKD",
    "norway": "NOR", "no": "NOR", "nor": "NOR",
    
    # O
    "oman": "OMA", "om": "OMA", "omn": "OMA",
    
    # P
    "pakistan": "PAK", "pk": "PAK", "pak": "PAK",
    "palau": "PLW", "pw": "PLW", "plw": "PLW",
    "palestine": "PLE", "ps": "PLE", "pse": "PLE",
    "panama": "PAN", "pa": "PAN", "pan": "PAN",
    "papua new guinea": "PNG", "pg": "PNG", "png": "PNG",
    "paraguay": "PAR", "py": "PAR", "pry": "PAR",
    "peru": "PER", "pe": "PER", "per": "PER",
    "philippines": "PHI", "ph": "PHI", "phl": "PHI",
    "poland": "POL", "pl": "POL", "pol": "POL",
    "portugal": "POR", "pt": "POR", "prt": "POR",
    "puerto rico": "PUR", "pr": "PUR", "pri": "PUR",
    
    # Q
    "qatar": "QAT", "qa": "QAT", "qat": "QAT",
    
    # R
    "romania": "ROU", "ro": "ROU", "rou": "ROU",
    "russia": "RUS", "ru": "RUS", "rus": "RUS",
    "russian federation": "RUS",
    "rwanda": "RWA", "rw": "RWA", "rwa": "RWA",
    
    # S
    "saint kitts and nevis": "SKN", "kn": "SKN", "kna": "SKN",
    "saint lucia": "LCA", "lc": "LCA", "lca": "LCA",
    "saint vincent and the grenadines": "VIN", "vc": "VIN", "vct": "VIN",
    "samoa": "SAM", "ws": "SAM", "wsm": "SAM",
    "san marino": "SMR", "sm": "SMR", "smr": "SMR",
    "sao tome and principe": "STP", "st": "STP", "stp": "STP",
    "saudi arabia": "KSA", "sa": "KSA", "sau": "KSA",
    "senegal": "SEN", "sn": "SEN", "sen": "SEN",
    "serbia": "SRB", "rs": "SRB", "srb": "SRB",
    "seychelles": "SEY", "sc": "SEY", "syc": "SEY",
    "sierra leone": "SLE", "sl": "SLE", "sle": "SLE",
    "singapore": "SGP", "sg": "SGP", "sgp": "SGP",
    "slovakia": "SVK", "sk": "SVK", "svk": "SVK",
    "slovenia": "SLO", "si": "SLO", "svn": "SLO",
    "solomon islands": "SOL", "sb": "SOL", "slb": "SOL",
    "somalia": "SOM", "so": "SOM", "som": "SOM",
    "south africa": "RSA", "za": "RSA", "zaf": "RSA",
    "south sudan": "SSD", "ss": "SSD", "ssd": "SSD",
    "spain": "ESP", "es": "ESP", "esp": "ESP",
    "sri lanka": "SRI", "lk": "SRI", "lka": "SRI",
    "sudan": "SUD", "sd": "SUD", "sdn": "SUD",
    "suriname": "SUR", "sr": "SUR", "sur": "SUR",
    "sweden": "SWE", "se": "SWE", "swe": "SWE",
    "switzerland": "SUI", "ch": "SUI", "che": "SUI",
    "syria": "SYR", "sy": "SYR", "syr": "SYR",
    
    # T
    "tajikistan": "TJK", "tj": "TJK", "tjk": "TJK",
    "tanzania": "TAN", "tz": "TAN", "tza": "TAN",
    "thailand": "THA", "th": "THA", "tha": "THA",
    "timor-leste": "TLS", "tl": "TLS", "tls": "TLS",
    "east timor": "TLS",
    "togo": "TOG", "tg": "TOG", "tgo": "TOG",
    "tonga": "TGA", "to": "TGA", "ton": "TGA",
    "trinidad and tobago": "TTO", "tt": "TTO", "tto": "TTO",
    "tunisia": "TUN", "tn": "TUN", "tun": "TUN",
    "turkey": "TUR", "tr": "TUR", "tur": "TUR",
    "turkmenistan": "TKM", "tm": "TKM", "tkm": "TKM",
    "tuvalu": "TUV", "tv": "TUV", "tuv": "TUV",
    
    # U
    "uganda": "UGA", "ug": "UGA", "uga": "UGA",
    "ukraine": "UKR", "ua": "UKR", "ukr": "UKR",
    "united arab emirates": "UAE", "ae": "UAE", "are": "UAE",
    "uae": "UAE",
    "united states": "USA", "us": "USA", "usa": "USA",
    "united states of america": "USA",
    "uruguay": "URU", "uy": "URU", "ury": "URU",
    "uzbekistan": "UZB", "uz": "UZB", "uzb": "UZB",
    
    # V
    "vanuatu": "VAN", "vu": "VAN", "vut": "VAN",
    "venezuela": "VEN", "ve": "VEN", "ven": "VEN",
    "vietnam": "VIE", "vn": "VIE", "vnm": "VIE",
    "virgin islands": "ISV", "vi": "ISV", "vir": "ISV",
    "us virgin islands": "ISV",
    
    # Y
    "yemen": "YEM", "ye": "YEM", "yem": "YEM",
    
    # Z
    "zambia": "ZAM", "zm": "ZAM", "zmb": "ZAM",
    "zimbabwe": "ZIM", "zw": "ZIM", "zwe": "ZIM",
}


def map_country_to_code(value: Optional[str]) -> Optional[str]:
    """Map country name, ISO-2, or ISO-3 code to 3-letter IOC/UCI code.
    
    Args:
        value: Country name or code (case-insensitive)
        
    Returns:
        3-letter IOC code, or original value if no mapping found
    """
    if not value:
        return value
        
    lookup = value.strip().lower()
    
    # Direct lookup
    if lookup in COUNTRY_DATA:
        return COUNTRY_DATA[lookup]
    
    # If already a valid 3-letter IOC code (uppercase in our values)
    if len(lookup) == 3 and lookup.upper() in set(COUNTRY_DATA.values()):
        return lookup.upper()
    
    # Fallback: return uppercase of original (for unknown codes)
    return value.upper()
