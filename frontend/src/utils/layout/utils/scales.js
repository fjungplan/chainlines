/**
 * Scale calculation utilities for the layout engine
 * Handles year range calculation and X-axis scaling
 */

/**
 * Calculate the year range from node data
 * @param {Array} nodes - Array of node objects with eras, founding_year, and dissolution_year
 * @returns {{min: number, max: number}} Year range object
 */
export function calculateYearRange(nodes) {
    const allYears = [];
    const eraYears = [];
    const foundingYears = [];
    const dissolutionYears = [];

    // Get years from eras
    nodes.forEach(node => {
        node.eras.forEach(era => {
            eraYears.push(era.year);
            allYears.push(era.year);
        });
        // Also include founding and dissolution years
        foundingYears.push(node.founding_year);
        allYears.push(node.founding_year);
        if (node.dissolution_year) {
            dissolutionYears.push(node.dissolution_year);
            allYears.push(node.dissolution_year);
        }
    });

    // Include current year so active teams extend to today
    const currentYear = new Date().getFullYear();
    allYears.push(currentYear);

    // Calculate range from actual data without arbitrary minimums
    const minYear = Math.min(...allYears, 1900);
    const maxYear = Math.max(...allYears);

    // Add +1 year to show the full span of the final year
    return {
        min: minYear,
        max: maxYear + 1
    };
}

/**
 * Create an X-axis scale function that maps years to pixel coordinates
 * @param {number} width - Total width of the visualization
 * @param {{min: number, max: number}} yearRange - Year range object
 * @param {number} stretchFactor - Horizontal stretch multiplier
 * @returns {Function} Scale function that takes a year and returns X coordinate
 */
export function createXScale(width, yearRange, stretchFactor) {
    // Map years to X coordinates
    const padding = 50;
    const { min, max } = yearRange;
    const span = max - min;
    const availableWidth = width - 2 * padding;
    const pixelsPerYear = (availableWidth / span) * stretchFactor;

    return (year) => {
        const range = max - min;
        const position = (year - min) / range;
        const result = padding + (position * (width - 2 * padding) * stretchFactor);
        return result;
    };
}
