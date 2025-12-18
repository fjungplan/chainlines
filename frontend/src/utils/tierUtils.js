/**
 * Historical configuration for UCI Team Tiers.
 * Ranges are inclusive.
 */
const TIER_HISTORY = [
    {
        start: 2020,
        end: 9999,
        system: "Modern Reforms",
        labels: {
            1: "UCI WorldTeam",
            2: "UCI ProTeam",
            3: "Continental"
        }
    },
    {
        start: 2015,
        end: 2019,
        system: "WorldTour Transition",
        labels: {
            1: "UCI WorldTeam",
            2: "Pro Continental",
            3: "Continental"
        }
    },
    {
        start: 2005,
        end: 2014,
        system: "UCI ProTour",
        labels: {
            1: "UCI ProTeam",
            2: "Pro Continental",
            3: "Continental"
        }
    },
    {
        start: 1996,
        end: 2004,
        system: "UCI Divisional",
        labels: {
            1: "Trade Team I",
            2: "Trade Team II",
            3: "Trade Team III"
        }
    },
    {
        start: 1990,
        end: 1995,
        system: "FICP / Unified",
        labels: {
            1: "Professional",
            2: "Professional", // Often no distinct 2nd tier in data, or handled ad-hoc
            3: "Amateur"
        }
    }
];

/**
 * Returns the historically accurate label for a given tier and season year.
 * @param {number} tierLevel - 1, 2, or 3
 * @param {number} year - The season year
 * @returns {string} The label (e.g., "WorldTeam", "GS1") or generic "Tier X" fallback
 */
export function getTierName(tierLevel, year) {
    if (!tierLevel) return null;

    const config = TIER_HISTORY.find(c => year >= c.start && year <= c.end);

    if (config && config.labels[tierLevel]) {
        return config.labels[tierLevel];
    }

    // Fallback for pre-1990 or unknown tiers
    return `Tier ${tierLevel}`;
}

/**
 * Returns the short code/abbreviation for a tier (optional usage)
 */
export function getTierAbbr(tierLevel, year) {
    const name = getTierName(tierLevel, year);
    if (!name) return "";

    // Custom abbreviations if simplified display is needed
    if (name === "UCI WorldTeam") return "WT";
    if (name === "UCI ProTeam") return "PRT";
    if (name === "Pro Continental") return "PCT";
    if (name === "Continental") return "CT";
    if (name === "Trade Team I") return "GS1";
    if (name === "Trade Team II") return "GS2";
    if (name === "Trade Team III") return "GS3";

    return name;
}
