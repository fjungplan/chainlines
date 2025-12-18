// Map of Alpha-3 codes to ISO 3166-1 Alpha-2 codes (lowercase)
// Required for flag-icons library
const CODE_MAP = {
    'FRA': 'fr',
    'ITA': 'it',
    'BEL': 'be',
    'ESP': 'es',
    'USA': 'us',
    'GBR': 'gb',
    'GER': 'de',
    'NED': 'nl',
    'AUS': 'au',
    'COL': 'co',
    'RUS': 'ru',
    'SUI': 'ch',
    'DEN': 'dk',
    'NOR': 'no',
    'POL': 'pl',
    'CAN': 'ca',
    'IRL': 'ie'
};

/**
 * Returns the Alpha-2 code for a given 3-letter country code.
 * Returns null if not found.
 */
export function getCountryCode(alpha3) {
    if (!alpha3) return null;
    return CODE_MAP[alpha3.toUpperCase()] || null;
}
