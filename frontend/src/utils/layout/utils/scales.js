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

    // Debug logging
    console.log('calculateYearRange: eraYears min/max:', Math.min(...eraYears), '/', Math.max(...eraYears));
    console.log('calculateYearRange: foundingYears min/max:', Math.min(...foundingYears), '/', Math.max(...foundingYears));
    console.log('calculateYearRange: dissolutionYears min/max:', Math.min(...dissolutionYears), '/', Math.max(...dissolutionYears));
    console.log('calculateYearRange: currentYear:', currentYear);
    console.log('calculateYearRange: final min/max:', minYear, '/', maxYear, 'returned range:', minYear, '-', maxYear + 1);

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

    console.log(`createXScale: this.width=${width}, padding=${padding}, availableWidth=${availableWidth}, stretchFactor=${stretchFactor}`);
    console.log(`  yearRange=${min}-${max}, span=${span}`);
    console.log(`  pixelsPerYear=${pixelsPerYear.toFixed(4)}`);
    console.log(`  Example: year 2000 should map to ${padding + ((2000 - min) / span) * availableWidth}, year 2008 should map to ${padding + ((2008 - min) / span) * availableWidth}`);

    return (year) => {
        const range = max - min;
        const position = (year - min) / range;
        const result = padding + (position * (width - 2 * padding) * stretchFactor);
        // Only log for key years to avoid spam
        if ([1900, 2000, 2007, 2008, 2025, 2026, max - 1].includes(year)) {
            console.log(`  xScale(${year}) = ${result.toFixed(2)} [position=${position.toFixed(4)}, effective_width=${width - 2 * padding}]`);
        }
        return result;
    };
}
